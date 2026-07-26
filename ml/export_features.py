"""
Export customer features from the governed BigQuery gold layer into a local
Parquet file that Feast's offline store reads from. This keeps Feast's
offline source pointed at the same certified numbers the BI dashboard and
RAG assistant use - one governed gold layer, three consumers.
"""
import os
from datetime import datetime, timezone
import pandas as pd
from google.cloud import bigquery

client = bigquery.Client(project="helios-platform-aakash")

query = """
    SELECT
        customer_id,
        recency_days,
        frequency,
        lifetime_value,
        avg_order_value,
        r_score,
        f_score,
        m_score,
        rfm_total,
        rfm_segment
    FROM `gold.mart_customer_ltv_rfm`
"""
df = client.query(query).to_dataframe()

# Churn label: At Risk / Lost segments are our ground truth for "churned"
df["churned"] = df["rfm_segment"].isin(["At Risk", "Lost"]).astype(int)

# Feast requires an event timestamp (and we add a created timestamp too);
# this is a single current snapshot, not a time-series of historical feature
# values, which is a reasonable simplification for this project's scope.
now = datetime.now(timezone.utc)
df["event_timestamp"] = now
df["created_timestamp"] = now

out_path = os.path.join(os.path.dirname(__file__), "..", "feature_repo", "data", "customer_features.parquet")
df.to_parquet(out_path, index=False)
print(f"Exported {len(df):,} customer feature rows to {out_path}")
print(f"Churn rate: {df['churned'].mean():.1%}")
