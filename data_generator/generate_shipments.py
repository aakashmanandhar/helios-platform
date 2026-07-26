import os
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(41)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "shipping")
os.makedirs(OUT_DIR, exist_ok=True)

conn = get_connection()
orders = pd.read_sql("SELECT order_id, order_date, status FROM orders WHERE status IN ('completed','refunded') ORDER BY order_id", conn)
conn.close()

n = len(orders)
order_ids = orders["order_id"].values
order_dates = pd.to_datetime(orders["order_date"]).values

CARRIERS = np.array(["UPS", "FedEx", "USPS"])
carriers = np.random.choice(CARRIERS, size=n, p=[0.40, 0.35, 0.25])

WAREHOUSES = np.array(["NE", "SE", "MW", "SW", "WC"])
origin_warehouse = np.random.choice(WAREHOUSES, size=n)

processing_days = np.random.randint(0, 3, size=n)
ship_date = pd.to_datetime(order_dates) + pd.to_timedelta(processing_days, unit="D")

transit_days_base = np.random.randint(2, 8, size=n)
estimated_delivery = ship_date + pd.to_timedelta(transit_days_base, unit="D")

late_mask = np.random.random(n) < 0.12
exception_mask = np.random.random(n) < 0.02
late_extra_days = np.where(late_mask, np.random.randint(1, 6, size=n), 0)
actual_delivery = estimated_delivery + pd.to_timedelta(late_extra_days, unit="D")

NOW = pd.Timestamp("2026-07-19")
still_in_transit_mask = (actual_delivery > NOW) & (~exception_mask)

status = np.where(exception_mask, "exception", "delivered")
status = np.where(still_in_transit_mask, "in_transit", status)

actual_delivery_final = pd.Series(actual_delivery)
actual_delivery_final = actual_delivery_final.where(~exception_mask, pd.NaT)
actual_delivery_final = actual_delivery_final.where(~still_in_transit_mask, pd.NaT)

shipments_df = pd.DataFrame({
    "shipment_id": [f"shp_{300000+i}" for i in range(n)],
    "order_id": order_ids,
    "carrier": carriers,
    "origin_warehouse": origin_warehouse,
    "ship_date": ship_date.strftime("%Y-%m-%d"),
    "estimated_delivery_date": estimated_delivery.strftime("%Y-%m-%d"),
    "actual_delivery_date": actual_delivery_final.dt.strftime("%Y-%m-%d"),
    "status": status,
})

shipments_df.to_csv(os.path.join(OUT_DIR, "carrier_shipments.csv"), index=False)
print(f"carrier_shipments.csv: {len(shipments_df):,} rows")
