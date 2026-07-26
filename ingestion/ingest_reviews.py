import os
from datetime import date
import pandas as pd

INGEST_DATE = date.today().isoformat()
BASE = os.path.dirname(__file__)
src_path = os.path.join(BASE, "..", "external_feeds", "reviews", "product_reviews.csv")
out_dir = os.path.join(BASE, "..", "lake", "bronze", "product_reviews", f"ingested_date={INGEST_DATE}")
os.makedirs(out_dir, exist_ok=True)

df = pd.read_csv(src_path)
out_path = os.path.join(out_dir, "part-0.parquet")
df.to_parquet(out_path, index=False)
print(f"product_reviews: {len(df):,} rows -> {out_path}")
