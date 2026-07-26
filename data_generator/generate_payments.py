import os
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(21)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "payments")
os.makedirs(OUT_DIR, exist_ok=True)

conn = get_connection()
orders = pd.read_sql("SELECT order_id, order_date, status, total_amount FROM orders ORDER BY order_id", conn)
conn.close()

n = len(orders)
order_ids = orders["order_id"].values
statuses = orders["status"].values
amounts = orders["total_amount"].astype(float).values
order_dates = pd.to_datetime(orders["order_date"]).values

# completed/refunded/pending always get a payment record; cancelled only 30% of the time
# (order cancelled before payment was ever attempted, the other 70%)
keep_mask = np.ones(n, dtype=bool)
cancelled_mask = statuses == "cancelled"
cancelled_random = np.random.random(n)
keep_mask[cancelled_mask] = cancelled_random[cancelled_mask] < 0.30

order_ids = order_ids[keep_mask]
statuses = statuses[keep_mask]
amounts = amounts[keep_mask]
order_dates = order_dates[keep_mask]
m = len(order_ids)

pay_status = np.select(
    [statuses == "completed", statuses == "refunded", statuses == "pending", statuses == "cancelled"],
    ["succeeded", "succeeded", "processing", "failed"],
    default="succeeded",
)
refunded_amount = np.where(statuses == "refunded", amounts, 0.0)

PAYMENT_METHODS = np.array(["card", "paypal", "apple_pay", "bank_transfer"])
methods = np.random.choice(PAYMENT_METHODS, size=m, p=[0.65, 0.20, 0.12, 0.03])

fee = np.where(pay_status == "succeeded", np.round(amounts * 0.029 + 0.30, 2), 0.0)

created_offset = pd.to_timedelta(np.random.randint(1, 45, size=m), unit="m")
created_at = pd.to_datetime(order_dates) + created_offset

payments_df = pd.DataFrame({
    "payment_id": [f"pi_{100000000+i}" for i in range(m)],
    "order_id": order_ids,
    "amount": np.round(amounts, 2),
    "currency": "usd",
    "status": pay_status,
    "payment_method": methods,
    "processor_fee": fee,
    "refunded_amount": np.round(refunded_amount, 2),
    "created_at": created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
})

# messiness: duplicate webhook deliveries, and a few orphaned order_ids (mismatched refs)
dup_rows = payments_df.sample(frac=0.004, random_state=1)
payments_df = pd.concat([payments_df, dup_rows], ignore_index=True)

orphan_idx = payments_df.sample(frac=0.002, random_state=2).index
payments_df.loc[orphan_idx, "order_id"] = payments_df.loc[orphan_idx, "order_id"] + 9_000_000

payments_df.to_csv(os.path.join(OUT_DIR, "stripe_payments.csv"), index=False)
print(f"stripe_payments.csv: {len(payments_df):,} rows")
