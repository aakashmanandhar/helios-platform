import os
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(31)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "support")
os.makedirs(OUT_DIR, exist_ok=True)

conn = get_connection()
orders = pd.read_sql("SELECT order_id, customer_id, order_date FROM orders ORDER BY order_id", conn)
customers = pd.read_sql("SELECT customer_id FROM customers ORDER BY customer_id", conn)
conn.close()

n_orders = len(orders)
order_ids = orders["order_id"].values
order_customer_ids = orders["customer_id"].values
order_dates = pd.to_datetime(orders["order_date"]).values

order_ticket_mask = np.random.random(n_orders) < 0.06
ticket_order_ids = order_ids[order_ticket_mask].astype(float)
ticket_customer_ids_from_orders = order_customer_ids[order_ticket_mask]
open_offsets = pd.to_timedelta(np.random.randint(1, 14, size=len(ticket_order_ids)), unit="D")
order_ticket_opened = pd.to_datetime(order_dates[order_ticket_mask]) + open_offsets
n_order_tickets = len(ticket_order_ids)

n_standalone = 30000
customer_ids_all = customers["customer_id"].values
standalone_customer_ids = np.random.choice(customer_ids_all, size=n_standalone)
START = pd.Timestamp("2024-07-20")
N_DAYS = 730
standalone_opened = START + pd.to_timedelta(np.random.randint(0, N_DAYS, size=n_standalone), unit="D") + pd.to_timedelta(np.random.randint(0, 86400, size=n_standalone), unit="s")

n_total = n_order_tickets + n_standalone
all_customer_ids = np.concatenate([ticket_customer_ids_from_orders, standalone_customer_ids])
all_order_ids = np.concatenate([ticket_order_ids, np.full(n_standalone, np.nan)])
all_opened = np.concatenate([order_ticket_opened.values, standalone_opened.values])

order_categories = np.random.choice(["shipping", "billing", "product_defect", "return_request"], size=n_order_tickets, p=[0.35, 0.20, 0.25, 0.20])
standalone_categories = np.random.choice(["account", "general_inquiry"], size=n_standalone, p=[0.45, 0.55])
categories = np.concatenate([order_categories, standalone_categories])

priorities = np.random.choice(["low", "medium", "high", "urgent"], size=n_total, p=[0.40, 0.35, 0.20, 0.05])
channels = np.random.choice(["email", "chat", "phone"], size=n_total, p=[0.5, 0.35, 0.15])

resolved_mask = np.random.random(n_total) < 0.90
resolution_hours = np.round(np.random.lognormal(mean=3.0, sigma=1.0, size=n_total), 1)
resolved_at = pd.to_datetime(all_opened) + pd.to_timedelta(resolution_hours, unit="h")

status = np.where(~resolved_mask, np.random.choice(["open", "pending"], size=n_total), "resolved")
closed_relabel = (status == "resolved") & (np.random.random(n_total) < 0.6)
status = np.where(closed_relabel, "closed", status)

mask_resolved = pd.Series(np.isin(status, ["resolved", "closed"]))
resolved_at_final = pd.Series(resolved_at).where(mask_resolved, pd.NaT)

csat_eligible = mask_resolved
csat_response_mask = csat_eligible & (pd.Series(np.random.random(n_total)) < 0.70)
raw_scores = np.clip(np.round(np.random.normal(loc=3.8, scale=1.0, size=n_total)), 1, 5)
csat_scores = pd.Series(raw_scores).where(csat_response_mask, np.nan)

tickets_df = pd.DataFrame({
    "ticket_id": [f"tkt_{200000+i}" for i in range(n_total)],
    "customer_id": all_customer_ids,
    "order_id": all_order_ids,
    "category": categories,
    "priority": priorities,
    "channel": channels,
    "status": status,
    "opened_at": pd.to_datetime(all_opened).strftime("%Y-%m-%d %H:%M:%S"),
    "resolved_at": resolved_at_final.dt.strftime("%Y-%m-%d %H:%M:%S"),
    "csat_score": csat_scores,
})

tickets_df = tickets_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
tickets_df.to_csv(os.path.join(OUT_DIR, "support_tickets.csv"), index=False)
print(f"support_tickets.csv: {len(tickets_df):,} rows")
