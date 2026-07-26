import os
import pandas as pd
from datetime import date

INGEST_DATE = date.today().isoformat()
BASE = os.path.dirname(__file__)
EXTERNAL_DIR = os.path.join(BASE, "..", "external_feeds", "marketing")
BRONZE_ROOT = os.path.join(BASE, "..", "lake", "bronze")

FEEDS = {
    "google_ads_daily.csv": "marketing_google",
    "meta_ads_daily.csv": "marketing_meta",
    "email_campaign_sends.csv": "marketing_email",
}

for filename, bronze_table in FEEDS.items():
    src_path = os.path.join(EXTERNAL_DIR, filename)
    df = pd.read_csv(src_path)
    out_dir = os.path.join(BRONZE_ROOT, bronze_table, f"ingested_date={INGEST_DATE}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "part-0.parquet")
    df.to_parquet(out_path, index=False)
    print(f"{bronze_table}: {len(df):,} rows -> {out_path}")

print("Marketing bronze ingestion complete.")
