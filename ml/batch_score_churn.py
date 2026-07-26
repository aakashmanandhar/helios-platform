"""
Batch-score every customer's churn probability using the trained model and
write predictions back into the governed BigQuery gold layer, so the BI
dashboard and RAG assistant can both reference the same certified score
instead of each maintaining their own copy of "is this customer at risk."

Features are pulled from the current snapshot in gold.mart_customer_ltv_rfm
- the same values Feast serves online - so the batch score and the live
single-customer endpoint (webapp/backend/churn) never disagree.
"""
import os
import joblib
import pandas as pd
from google.cloud import bigquery

PROJECT_ID = "helios-platform-aakash"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "churn_model.joblib")
DEST_TABLE = f"{PROJECT_ID}.gold.mart_churn_predictions"

bundle = joblib.load(MODEL_PATH)
pipeline = bundle["pipeline"]
feature_cols = bundle["feature_cols"]

client = bigquery.Client(project=PROJECT_ID)

df = client.query("""
    SELECT
        customer_id,
        first_name,
        last_name,
        region,
        recency_days,
        frequency,
        lifetime_value,
        avg_order_value,
        rfm_segment
    FROM `gold.mart_customer_ltv_rfm`
""").to_dataframe()

X = df[feature_cols].fillna(0)
df["churn_probability"] = pipeline.predict_proba(X)[:, 1].round(4)
df["risk_band"] = pd.cut(
    df["churn_probability"],
    bins=[-0.01, 0.3, 0.6, 1.0],
    labels=["Low", "Medium", "High"],
)
df["scored_at"] = pd.Timestamp.utcnow()

out_cols = [
    "customer_id", "first_name", "last_name", "region",
    "rfm_segment", "churn_probability", "risk_band", "scored_at",
]
out = df[out_cols]

job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
job = client.load_table_from_dataframe(out, DEST_TABLE, job_config=job_config)
job.result()

print(f"Wrote {len(out):,} churn predictions to {DEST_TABLE}")
print(out["risk_band"].value_counts())
print(out.sort_values("churn_probability", ascending=False).head(5))
