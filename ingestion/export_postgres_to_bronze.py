import os
import sys
import decimal
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data_generator"))

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import date
from db import get_connection

INGEST_DATE = date.today().isoformat()
BRONZE_ROOT = os.path.join(os.path.dirname(__file__), "..", "lake", "bronze")

TABLES = ["customers", "products", "orders", "order_items", "inventory"]
BATCH_SIZE = 200_000

def fix_decimal_columns(df):
    for col in df.columns:
        if df[col].dtype == object:
            non_null = df[col].dropna()
            if not non_null.empty and isinstance(non_null.iloc[0], decimal.Decimal):
                df[col] = df[col].astype(float)
    return df

def export_table(conn, table):
    out_dir = os.path.join(BRONZE_ROOT, table, f"ingested_date={INGEST_DATE}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "part-0.parquet")

    cur = conn.cursor(name=f"export_{table}")
    cur.itersize = BATCH_SIZE
    cur.execute(f"SELECT * FROM {table}")

    writer = None
    colnames = None
    total = 0
    while True:
        rows = cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        if colnames is None:
            colnames = [desc[0] for desc in cur.description]
        df = pd.DataFrame(rows, columns=colnames)
        df = fix_decimal_columns(df)
        arrow_table = pa.Table.from_pandas(df, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(out_path, arrow_table.schema)
        writer.write_table(arrow_table)
        total += len(df)
        print(f"  {table}: wrote {total:,} rows so far...")
    if writer:
        writer.close()
    cur.close()
    print(f"{table}: done, {total:,} rows -> {out_path}")

if __name__ == "__main__":
    conn = get_connection()
    conn.autocommit = False
    for t in TABLES:
        print(f"Exporting {t}...")
        export_table(conn, t)
    conn.commit()
    conn.close()
    print("Bronze export complete.")
