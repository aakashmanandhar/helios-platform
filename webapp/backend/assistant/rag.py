"""
Phase 7: hybrid retrieval + Gemini synthesis.

Retrieval: vector search over ai.document_chunks (pgvector) - the same
embedded tickets/reviews/KB docs built in Phase 5.

Structured lookup: a genuine tool the model can call (lookup_customer_history)
that queries the governed BigQuery gold layer for a specific customer's order
history, LTV/RFM segment, and open support tickets. This is what makes the
retrieval "hybrid" rather than vector-search-only, matching the platform
design's "vector search + SQL tool over gold" serving pattern.
"""
import psycopg2
from functools import lru_cache
from django.conf import settings
from google import genai
from google.genai import types
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer

from helios_dashboard.bq_client import get_bq_client

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_LOCATION = "us-central1"


@lru_cache(maxsize=1)
def get_embed_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def get_pg_connection():
    return psycopg2.connect(
        host=settings.POSTGRES["HOST"],
        port=settings.POSTGRES["PORT"],
        dbname=settings.POSTGRES["NAME"],
        user=settings.POSTGRES["USER"],
        password=settings.POSTGRES["PASSWORD"],
    )


def retrieve_chunks(question, top_k=6):
    model = get_embed_model()
    emb = model.encode(question)
    conn = get_pg_connection()
    register_vector(conn)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT source_type, source_id, chunk_text, customer_id, order_id, product_id,
               embedding <=> %s AS distance
        FROM ai.document_chunks
        ORDER BY embedding <=> %s
        LIMIT %s
        """,
        (emb, emb, top_k),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "source_type": r[0], "source_id": r[1], "chunk_text": r[2],
            "customer_id": r[3], "order_id": r[4], "product_id": r[5],
            "distance": float(r[6]),
        }
        for r in rows
    ]


def lookup_customer_history(customer_id: str) -> str:
    """Look up a customer's order history, lifetime value, RFM segment, and any
    open support tickets from the governed gold layer. Call this when a retrieved
    ticket or review mentions a specific customer_id and more structured context
    (order count, refund/cancellation history, open ticket status) would help
    answer the question precisely."""
    try:
        cid = int(customer_id)
    except (TypeError, ValueError):
        return f"'{customer_id}' is not a valid customer id."

    client = get_bq_client()

    profile_rows = list(client.query(f"""
        SELECT c.first_name, c.last_name, c.region,
               r.frequency, r.lifetime_value, r.rfm_segment, r.recency_days
        FROM `gold.dim_customer` c
        LEFT JOIN `gold.mart_customer_ltv_rfm` r ON r.customer_id = c.customer_id
        WHERE c.customer_id = {cid}
        LIMIT 1
    """).result())
    if not profile_rows:
        return f"No customer found with id {cid}."
    p = profile_rows[0]

    order_rows = list(client.query(f"""
        SELECT status, COUNT(*) AS cnt
        FROM `gold.fact_orders`
        WHERE customer_id = {cid}
        GROUP BY status
    """).result())
    order_summary = ", ".join(f"{o.cnt} {o.status}" for o in order_rows) or "no orders"

    ticket_rows = list(client.query(f"""
        SELECT ticket_id, category, status, priority
        FROM `gold.fact_support_tickets`
        WHERE customer_id = {cid} AND status IN ('open', 'pending')
    """).result())
    ticket_summary = "; ".join(f"{t.ticket_id} ({t.category}, {t.priority})" for t in ticket_rows) or "none open"

    ltv = f"${p.lifetime_value:,.2f}" if p.lifetime_value is not None else "unknown"
    return (
        f"Customer {p.first_name} {p.last_name} ({p.region}). "
        f"Lifetime value: {ltv}. RFM segment: {p.rfm_segment or 'unscored'}. "
        f"Last order {p.recency_days if p.recency_days is not None else 'unknown'} days ago. "
        f"Order history: {order_summary}. Open support tickets: {ticket_summary}."
    )


def answer_question(question, top_k=6):
    chunks = retrieve_chunks(question, top_k=top_k)

    def format_chunk(i, c):
        meta_bits = []
        if c.get("customer_id") is not None:
            meta_bits.append(f"customer_id={int(c['customer_id'])}")
        if c.get("order_id") is not None:
            meta_bits.append(f"order_id={int(c['order_id'])}")
        if c.get("product_id") is not None:
            meta_bits.append(f"product_id={int(c['product_id'])}")
        meta = f" [{', '.join(meta_bits)}]" if meta_bits else ""
        return f"[{i + 1}] (source: {c['source_type']} {c['source_id']}{meta}) {c['chunk_text']}"

    context_block = "\n\n".join(format_chunk(i, c) for i, c in enumerate(chunks))

    system_prompt = (
        "You are a support and analytics assistant for NorthStar Retail. Answer the user's question "
        "grounded in the retrieved context below. Cite sources inline using bracket numbers like [1], [2] "
        "matching the retrieved context list. Each retrieved chunk includes its customer_id/order_id/product_id "
        "metadata in brackets when available - use that customer_id directly with the lookup_customer_history "
        "tool rather than trying to infer it from order numbers in the text. When a question asks you to "
        "compare or characterize multiple customers (e.g. are they loyal or new), call the tool for each "
        "relevant customer_id you have before concluding you lack enough information. If the context and tool "
        "still don't contain enough information to answer confidently, say so honestly rather than guessing.\n\n"
        f"Retrieved context:\n{context_block}"
    )

    client = genai.Client(vertexai=True, project=settings.GCP_PROJECT_ID, location=GEMINI_LOCATION)
    resp = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[lookup_customer_history],
        ),
    )

    return {
        "answer": resp.text,
        "citations": [
            {
                "ref": i + 1, "source_type": c["source_type"], "source_id": c["source_id"],
                "snippet": c["chunk_text"][:200],
            }
            for i, c in enumerate(chunks)
        ],
    }
