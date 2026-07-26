import os
from datetime import date, datetime
from pathlib import Path
import pandas as pd

INGEST_DATE = date.today().isoformat()
BASE = os.path.dirname(__file__)
kb_dir = Path(os.path.join(BASE, "..", "knowledge_base"))
out_dir = os.path.join(BASE, "..", "lake", "bronze", "knowledge_base_articles", f"ingested_date={INGEST_DATE}")
os.makedirs(out_dir, exist_ok=True)

rows = []
for i, path in enumerate(sorted(kb_dir.glob("*.md"))):
    text = path.read_text()
    first_line = text.splitlines()[0] if text.splitlines() else path.stem
    title = first_line.lstrip("#").strip()
    rows.append({
        "doc_id": f"kb_{i+1:03d}",
        "doc_name": path.stem,
        "title": title,
        "content": text,
        "category": "policy",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })

df = pd.DataFrame(rows)
out_path = os.path.join(out_dir, "part-0.parquet")
df.to_parquet(out_path, index=False)
print(f"knowledge_base_articles: {len(df):,} rows -> {out_path}")
print(df[["doc_id", "doc_name", "title"]].to_string(index=False))
