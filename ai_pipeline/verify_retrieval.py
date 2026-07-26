"""
Quick sanity check: embed a few realistic questions and confirm the vector
store returns sensible nearest neighbors. This is a manual smoke test now;
it becomes the seed for the retrieval-quality eval set in the Phase 9
DataOps hardening work (known query -> expected chunk, run in CI).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from db import get_connection
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

TEST_QUERIES = [
    "how long do I have to return an item",
    "my package never arrived even though tracking says delivered",
    "can I combine loyalty points with a promo code",
    "the product I received was broken",
]

conn = get_connection()
register_vector(conn)
cur = conn.cursor()

for query in TEST_QUERIES:
    emb = model.encode(query)
    cur.execute("""
        SELECT source_type, source_id, chunk_text, embedding <=> %s AS distance
        FROM ai.document_chunks
        ORDER BY embedding <=> %s
        LIMIT 3
    """, (emb, emb))
    print(f"\n=== Query: {query!r} ===")
    for source_type, source_id, chunk_text, distance in cur.fetchall():
        preview = chunk_text[:100].replace("\n", " ")
        print(f"  [{distance:.3f}] ({source_type}:{source_id}) {preview}...")

cur.close()
conn.close()
