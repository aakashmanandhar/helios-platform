"""
Phase 5: unstructured pipeline - PII scrub -> chunk -> embed -> vector store.

Reads ticket descriptions, review text, and KB docs from the governed gold/
silver layer (not raw bronze), so the vector store's metadata (customer_id,
order_id, product_id) is guaranteed consistent with what the BI layer and
any future feature store would reference - this is the "same governed gold
layer serving multiple consumers" principle from the platform design.

Sample sizes are deliberately capped (see SAMPLE_SIZE below) - proving out
the pipeline doesn't require embedding the full 270K tickets / 850K reviews
on a CPU-only local machine. Same reasoning as the CI data-generation scale-
down: prove correctness, don't burn wall-clock time proving it at a volume
this project doesn't need.
"""
import os
import sys
import time

import duckdb
import numpy as np
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection
from pii_scrub import scrub_pii
from chunk_kb import chunk_markdown

SAMPLE_SIZE = 20000
DUCKDB_PATH = os.path.join(os.path.dirname(__file__), "..", "warehouse", "helios.duckdb")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
BATCH_SIZE = 128


def load_source_rows():
    con = duckdb.connect(DUCKDB_PATH, read_only=True)

    tickets = con.execute(f"""
        SELECT ticket_id, customer_id, order_id, category, priority, description
        FROM gold.fact_support_tickets
        WHERE description IS NOT NULL
        ORDER BY random()
        LIMIT {SAMPLE_SIZE}
    """).fetchdf()

    reviews = con.execute(f"""
        SELECT review_id, customer_id, order_id, product_id, rating, review_text
        FROM gold.fact_product_reviews
        WHERE has_text = true
        ORDER BY random()
        LIMIT {SAMPLE_SIZE}
    """).fetchdf()

    kb_docs = con.execute("""
        SELECT doc_id, doc_name, title, content
        FROM silver.stg_knowledge_base_articles
    """).fetchdf()

    con.close()
    return tickets, reviews, kb_docs


def build_chunks(tickets, reviews, kb_docs):
    chunks = []
    pii_scrubbed_count = 0

    for row in tickets.itertuples():
        text, was_scrubbed = scrub_pii(row.description)
        pii_scrubbed_count += int(was_scrubbed)
        chunks.append({
            "source_type": "ticket",
            "source_id": row.ticket_id,
            "chunk_index": 0,
            "chunk_text": text,
            "customer_id": row.customer_id,
            "order_id": row.order_id if row.order_id == row.order_id else None,  # NaN check
            "product_id": None,
        })

    for row in reviews.itertuples():
        text, was_scrubbed = scrub_pii(row.review_text)
        pii_scrubbed_count += int(was_scrubbed)
        chunks.append({
            "source_type": "review",
            "source_id": row.review_id,
            "chunk_index": 0,
            "chunk_text": text,
            "customer_id": row.customer_id,
            "order_id": row.order_id if row.order_id == row.order_id else None,
            "product_id": row.product_id,
        })

    for row in kb_docs.itertuples():
        for kb_chunk in chunk_markdown(row.doc_id, row.title, row.content):
            chunks.append({
                "source_type": "kb_article",
                "source_id": kb_chunk["source_id"],
                "chunk_index": kb_chunk["chunk_index"],
                "chunk_text": kb_chunk["chunk_text"],
                "customer_id": None,
                "order_id": None,
                "product_id": None,
            })

    print(f"PII-scrubbed rows: {pii_scrubbed_count:,} / {len(tickets) + len(reviews):,} ticket+review rows")
    return chunks


def embed_chunks(chunks):
    model = SentenceTransformer(EMBEDDING_MODEL)
    texts = [c["chunk_text"] for c in chunks]
    print(f"Embedding {len(texts):,} chunks with {EMBEDDING_MODEL} (batch size {BATCH_SIZE})...")
    start = time.time()
    embeddings = model.encode(texts, batch_size=BATCH_SIZE, show_progress_bar=True, convert_to_numpy=True)
    elapsed = time.time() - start
    print(f"Embedding done in {elapsed:.1f}s ({len(texts) / elapsed:.1f} chunks/sec)")
    return embeddings


def load_to_pgvector(chunks, embeddings):
    conn = get_connection()
    register_vector(conn)
    cur = conn.cursor()

    cur.execute("TRUNCATE ai.document_chunks RESTART IDENTITY")

    rows = [
        (
            c["source_type"], c["source_id"], c["chunk_index"], c["chunk_text"],
            c["customer_id"], c["order_id"], c["product_id"], emb,
        )
        for c, emb in zip(chunks, embeddings)
    ]

    execute_values(
        cur,
        """
        INSERT INTO ai.document_chunks
            (source_type, source_id, chunk_index, chunk_text, customer_id, order_id, product_id, embedding)
        VALUES %s
        """,
        rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s)",
        page_size=500,
    )
    conn.commit()
    cur.close()
    conn.close()


def main():
    print("Loading source rows from local DuckDB gold/silver layer...")
    tickets, reviews, kb_docs = load_source_rows()
    print(f"tickets: {len(tickets):,}, reviews: {len(reviews):,}, kb_docs: {len(kb_docs):,}")

    chunks = build_chunks(tickets, reviews, kb_docs)
    print(f"total chunks to embed: {len(chunks):,}")

    embeddings = embed_chunks(chunks)
    load_to_pgvector(chunks, embeddings)

    print("Done. Vector store loaded into Postgres ai.document_chunks.")


if __name__ == "__main__":
    main()
