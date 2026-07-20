import io
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(7)

WAREHOUSES = ["NE", "SE", "MW", "SW", "WC"]

conn = get_connection()
products = pd.read_sql("SELECT product_id FROM products ORDER BY product_id", conn)
product_ids = products["product_id"].values
n_products = len(product_ids)

rows = []
for wh in WAREHOUSES:
    stock = np.random.lognormal(mean=4.5, sigma=1.0, size=n_products).astype(int)
    stock = np.clip(stock, 0, 3000)

    stockout_mask = np.random.random(n_products) < 0.04
    stock[stockout_mask] = np.random.randint(0, 5, size=stockout_mask.sum())

    overstock_mask = np.random.random(n_products) < 0.04
    stock[overstock_mask] = np.random.randint(1000, 3000, size=overstock_mask.sum())

    reorder_point = np.round(np.random.uniform(0.15, 0.30, size=n_products) * np.clip(stock, 20, None)).astype(int)

    rows.append(pd.DataFrame({
        "product_id": product_ids,
        "warehouse_code": wh,
        "stock_qty": stock,
        "reorder_point": reorder_point,
    }))

inventory_df = pd.concat(rows, ignore_index=True)

def copy_df(conn, df, table, columns):
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, columns=columns)
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)", buf)
    conn.commit()

print(f"Loading {len(inventory_df):,} inventory rows...")
copy_df(conn, inventory_df, "inventory", ["product_id", "warehouse_code", "stock_qty", "reorder_point"])
conn.close()
print("Done.")
