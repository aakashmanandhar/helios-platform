"""
Build a leakage-free churn training set directly from fact_orders.

Why this exists: the first version of the churn model used
`churned = 1 if rfm_segment in ('At Risk', 'Lost')` from
mart_customer_ltv_rfm as the label. But rfm_segment is derived from
r_score, which is `ntile(5) over (order by recency_days desc)` - and
both 'At Risk' and 'Lost' require r_score <= 2. That means the label
was (almost) a deterministic function of recency_days, which was also
one of the training features. Result: 1.00 precision/recall/f1 - not a
real model, just the label rediscovering itself.

Fix: a genuine time-based holdout.
  - cutoff = max(order_date) across completed orders, minus 90 days
  - FEATURES (frequency, lifetime_value, avg_order_value, recency_days)
    computed only from orders strictly BEFORE the cutoff
  - LABEL: churned = 1 if the customer placed no completed order in the
    90 days at/after the cutoff, despite having ordered before it
  - Customers with zero orders before the cutoff are excluded - there's
    no prior behavior to predict from

Feature column names intentionally match what Feast serves online
(recency_days, frequency, lifetime_value, avg_order_value) so the
model's input contract is identical between training and serving -
only how they're computed for training differs (point-in-time here,
current-snapshot in Feast).
"""
import os
from google.cloud import bigquery

client = bigquery.Client(project="helios-platform-aakash")

query = """
    WITH bounds AS (
        SELECT DATE_SUB(MAX(order_date), INTERVAL 90 DAY) AS cutoff_date
        FROM `gold.fact_orders`
        WHERE status = 'completed'
    ),
    pre_cutoff AS (
        SELECT
            o.customer_id,
            COUNT(*) AS frequency,
            SUM(o.total_amount) AS monetary,
            MAX(o.order_date) AS last_order_date_pre_cutoff
        FROM `gold.fact_orders` o
        CROSS JOIN bounds b
        WHERE o.status = 'completed' AND o.order_date < b.cutoff_date
        GROUP BY o.customer_id
    ),
    post_cutoff AS (
        SELECT DISTINCT o.customer_id
        FROM `gold.fact_orders` o
        CROSS JOIN bounds b
        WHERE o.status = 'completed' AND o.order_date >= b.cutoff_date
    )
    SELECT
        p.customer_id,
        p.frequency,
        ROUND(p.monetary, 2) AS lifetime_value,
        ROUND(p.monetary / NULLIF(p.frequency, 0), 2) AS avg_order_value,
        DATE_DIFF((SELECT cutoff_date FROM bounds), p.last_order_date_pre_cutoff, DAY) AS recency_days,
        CASE WHEN post.customer_id IS NULL THEN 1 ELSE 0 END AS churned
    FROM pre_cutoff p
    LEFT JOIN post_cutoff post ON post.customer_id = p.customer_id
"""

df = client.query(query).to_dataframe()

out_path = os.path.join(os.path.dirname(__file__), "data", "churn_training_set.parquet")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
df.to_parquet(out_path, index=False)

print(f"Exported {len(df):,} customer rows to {out_path}")
print(f"Churn rate (no order in most recent 90-day window): {df['churned'].mean():.1%}")
print(df[["frequency", "lifetime_value", "avg_order_value", "recency_days", "churned"]].describe())
