# Phase 9 — DataOps Hardening

## Lineage

`dbt docs generate` builds a full catalog and dependency graph across the project:
36 models, 2 seeds, 63 data tests, 15 sources, spanning bronze → silver → gold for
both structured (orders, customers, marketing, payments, support, shipments, weather,
clickstream) and the newer unstructured sources (reviews, KB articles). `dbt docs serve`
exposes the interactive DAG and column-level lineage locally — "why does this number
look wrong" or "what feeds gold.mart_customer_ltv_rfm" is answerable by clicking through
the graph rather than grepping SQL.

## Chaos test: does the quality gate actually catch bad data?

Two experiments were run directly against the `orders` bronze parquet files (bypassing
the generator, simulating a real upstream fault) to find out.

**Attempt 1 — duplicate primary key.** Appended a duplicate `order_id` row to the
2026-07-20 bronze partition. `dbt build` reported PASS=20/ERROR=0 — no failure. Traced
it down: `stg_orders.sql` already runs `row_number() over (partition by order_id order
by updated_at desc)` and keeps `rn = 1`, i.e. deduplication was already built into the
silver layer (per the original architecture's "cleaned, deduplicated" requirement for
silver). The duplicate was silently and correctly resolved rather than tripping a test.
Genuine finding, not a bug — the pipeline already handles the "upstream system replays
a record" failure mode.

**Attempt 2 — orphaned foreign key.** Changed one order's `customer_id` to a value
(999999999) that doesn't exist in `dim_customer` — simulating a customer record that
was deleted/never synced upstream while their order data kept flowing. Result:
Both the staging and mart-level `relationships` tests failed as `ERROR` (not a soft
warning), which in a real CI/CD pipeline would block the run from promoting to
production before the bad row ever reached `gold.fact_orders`, the BI dashboard, or the
RAG assistant. Reverted the file afterward; a clean rebuild immediately returned to
PASS=20/ERROR=0.

(One pre-existing warning appears in every run above and is unrelated to either
experiment: `relationships_fact_payments_order_id` warns because payments records exist
for orders outside the sampled order date range — a known, accepted data-generation
artifact, intentionally configured as `warn` rather than `error`.)

## Freshness

Added a `loaded_at_field`/`freshness` block to the `orders` source (`updated_at`,
warn after 24h, error after 72h). `dbt source freshness` passes:
## Cost

Pulled real numbers from `INFORMATION_SCHEMA.JOBS_BY_PROJECT` (region `us-central1`,
where the gold/silver/bronze datasets live) rather than estimating:

- 835 BigQuery query jobs run today (project build day)
- 22.35 GB billed
- ~$0.14 estimated cost at on-demand pricing ($6.25/TiB)

Embeddings for the unstructured/RAG pipeline (40,047 KB/ticket/review chunks) were
generated locally via `sentence-transformers` (`all-MiniLM-L6-v2`), so that layer has
zero third-party API cost. The RAG assistant uses Gemini via Vertex AI, a first-party
model with default project quota — no manual quota request needed, unlike the
Claude-on-Vertex path that was abandoned earlier in the build for exactly that reason.
