import os
import pandas as pd
from datetime import date

INGEST_DATE = date.today().isoformat()
BASE = os.path.dirname(__file__)
src_path = os.path.join(BASE, "..", "external_feeds", "support", "support_tickets.csv")
out_dir = os.path.join(BASE, "..", "lake", "bronze", "support_tickets", f"ingested_date={INGEST_DATE}")
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(src_path)
out_path = os.path.join(out_dir, "part-0.parquet")
df.to_parquet(out_path, index=False)
print(f"support_tickets: {len(df):,} rows -> {out_path}")
