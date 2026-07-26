import os
import pandas as pd
from datetime import date

INGEST_DATE = date.today().isoformat()
BASE = os.path.dirname(__file__)
src_path = os.path.join(BASE, "..", "external_feeds", "payments", "stripe_payments.csv")
out_dir = os.path.join(BASE, "..", "lake", "bronze", "payments", f"ingested_date={INGEST_DATE}")
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(src_path)
out_path = os.path.join(out_dir, "part-0.parquet")
df.to_parquet(out_path, index=False)
print(f"payments: {len(df):,} rows -> {out_path}")
