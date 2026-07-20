import io
import time
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(42)
t0 = time.time()

N_ORDERS = 4_000_000

conn = get_connection()

print("Loading customers and products for reference...")
customers = pd.read_sql("SELECT customer_id, signup_date FROM customers ORDER BY customer_id", conn)
products = pd.read_sql("SELECT product_id, unit_price FROM products ORDER BY product_id", conn)

n_customers = len(customers)
n_products = len(products)
customer_ids = customers["customer_id"].values
product_ids = products["product_id"].values
product_prices = products["unit_price"].astype(float).values

# some customers buy far more than others
cust_weights = np.random.exponential(scale=1.0, size=n_customers)
cust_weights = cust_weights / cust_weights.sum()

# power-law product popularity: a few bestsellers, long tail
ranks = np.arange(1, n_products + 1)
prod_weights = 1 / np.power(ranks, 0.9)
np.random.shuffle(prod_weights)
prod_weights = prod_weights / prod_weights.sum()

# 2 years of history, with Nov/Dec holiday spike, Jan/Feb dip, weekend bump
START = pd.Timestamp("2024-07-20")
N_DAYS = 730
day_dates = START + pd.to_timedelta(np.arange(N_DAYS), unit="D")
month_weight = np.where(np.isin(day_dates.month, [11, 12]), 1.6,
                 np.where(np.isin(day_dates.month, [1, 2]), 0.8, 1.0))
weekend_weight = np.where(day_dates.dayofweek >= 5, 1.2, 1.0)
day_weight = month_weight * weekend_weight
day_weight = day_weight / day_weight.sum()

print(f"Generating {N_ORDERS:,} orders...")
order_customer_idx = np.random.choice(n_customers, size=N_ORDERS, p=cust_weights)
order_customer_ids = customer_ids[order_customer_idx]
order_day_offsets = np.random.choice(N_DAYS, size=N_ORDERS, p=day_weight)
order_dates = START + pd.to_timedelta(order_day_offsets, unit="D") + pd.to_timedelta(np.random.randint(0, 86400, size=N_ORDERS), unit="s")

statuses = np.random.choice(["completed", "cancelled", "pending", "refunded"], size=N_ORDERS, p=[0.85, 0.08, 0.05, 0.02])
channels = np.random.choice(["organic", "paid_search", "direct", "email", "affiliate"], size=N_ORDERS, p=[0.35, 0.25, 0.20, 0.12, 0.08])

order_ids = np.arange(1, N_ORDERS + 1)  # table is empty, BIGSERIAL will assign these in this exact order

items_per_order = np.random.poisson(1.3, size=N_ORDERS) + 1
total_items = int(items_per_order.sum())
print(f"Generating {total_items:,} order items...")

item_order_ids = np.repeat(order_ids, items_per_order)
item_product_idx = np.random.choice(n_products, size=total_items, p=prod_weights)
item_product_ids = product_ids[item_product_idx]
item_quantities = np.random.choice([1, 2, 3, 4, 5], size=total_items, p=[0.5, 0.25, 0.15, 0.07, 0.03])
price_variance = np.random.uniform(0.92, 1.0, size=total_items)
item_unit_prices = np.round(product_prices[item_product_idx] * price_variance, 2)
item_line_totals = np.round(item_quantities * item_unit_prices, 2)

order_items_df = pd.DataFrame({
    "order_id": item_order_ids,
    "product_id": item_product_ids,
    "quantity": item_quantities,
    "unit_price": item_unit_prices,
    "line_total": item_line_totals,
})

print("Aggregating order subtotals...")
subtotals = order_items_df.groupby("order_id")["line_total"].sum().reindex(order_ids, fill_value=0).values

discount_flag = np.random.random(N_ORDERS) < 0.2
discounts = np.where(discount_flag, np.round(subtotals * np.random.uniform(0.05, 0.20, size=N_ORDERS), 2), 0.0)
shipping_fees = np.where(subtotals > 50, 0.0, 5.99)
taxable = subtotals - discounts
taxes = np.round(taxable * 0.07, 2)
totals = np.round(taxable + shipping_fees + taxes, 2)

orders_df = pd.DataFrame({
    "customer_id": order_customer_ids,
    "order_date": order_dates,
    "status": statuses,
    "channel": channels,
    "subtotal": np.round(subtotals, 2),
    "discount": discounts,
    "shipping_fee": shipping_fees,
    "tax": taxes,
    "total_amount": totals,
})

def copy_df(conn, df, table, columns):
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, columns=columns)
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)", buf)
    conn.commit()

print("Loading orders into Postgres...")
copy_df(conn, orders_df, "orders", ["customer_id", "order_date", "status", "channel", "subtotal", "discount", "shipping_fee", "tax", "total_amount"])

print("Loading order_items into Postgres...")
copy_df(conn, order_items_df, "order_items", ["order_id", "product_id", "quantity", "unit_price", "line_total"])

conn.close()
print(f"Done in {time.time() - t0:.1f}s.")
