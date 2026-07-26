import os
import numpy as np
import pandas as pd
from faker import Faker
from db import get_connection

np.random.seed(31)
fake = Faker()
Faker.seed(31)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "support")
os.makedirs(OUT_DIR, exist_ok=True)

conn = get_connection()
orders = pd.read_sql("SELECT order_id, customer_id, order_date FROM orders ORDER BY order_id", conn)
customers = pd.read_sql("SELECT customer_id FROM customers ORDER BY customer_id", conn)
# one representative product per order (first item), for product-related ticket text
order_products = pd.read_sql("""
    SELECT DISTINCT ON (oi.order_id) oi.order_id, p.product_name
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    ORDER BY oi.order_id, oi.order_item_id
""", conn)
conn.close()

order_product_map = dict(zip(order_products["order_id"], order_products["product_name"]))

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

TEMPLATES = {
    "shipping": [
        "My order #{order_id} was supposed to arrive days ago but it's still not here. Can you check the status?",
        "The tracking for order #{order_id} hasn't updated in almost a week. Getting worried it's lost.",
        "Order #{order_id} arrived several days late and the box was crushed on one corner.",
        "I never received order #{order_id}, tracking says delivered but nothing showed up at my address.",
    ],
    "billing": [
        "I was charged twice for order #{order_id}, can someone refund the duplicate charge?",
        "The total on my order #{order_id} doesn't match what I was actually charged on my card statement.",
        "Why was I charged a restocking fee on order #{order_id}? I wasn't told about that upfront.",
        "My promo code didn't apply on order #{order_id}, I ended up paying full price.",
    ],
    "product_defect": [
        "The {product} from order #{order_id} stopped working after only a few days of normal use.",
        "Received the {product} (order #{order_id}) and it arrived with a visible crack, looks damaged before shipping.",
        "The {product} I ordered (#{order_id}) doesn't match the description at all, feels like a completely different item.",
        "My {product} from order #{order_id} is missing parts, the box was sealed but the contents were incomplete.",
    ],
    "return_request": [
        "I'd like to return the {product} from order #{order_id}, it's not what I expected.",
        "Can I get a return label for order #{order_id}? It just doesn't fit / work for my needs.",
        "Requesting a refund on order #{order_id}, decided I don't need the {product} after all.",
        "Is order #{order_id} still eligible for a return? It's been a couple weeks since it arrived.",
    ],
    "account": [
        "I can't log into my account, the password reset email never arrives.",
        "Someone else seems to have access to my account, I see order history I don't recognize.",
        "Can you merge my two accounts? I accidentally signed up twice with different emails.",
        "My saved payment method keeps getting declined even though the card is valid and not expired.",
    ],
    "general_inquiry": [
        "Do you ship to APO/FPO military addresses?",
        "What's your price match policy if I find the same item cheaper somewhere else?",
        "How do I redeem loyalty points on my next order?",
        "Is there a way to get a copy of an old invoice for tax purposes?",
    ],
}

def make_description(category, order_id, rng):
    template = rng.choice(TEMPLATES[category])
    product = order_product_map.get(order_id, "item") if not np.isnan(order_id) else None
    text = template.format(order_id=int(order_id) if not np.isnan(order_id) else "", product=product or "item")
    # deliberate PII leakage in a small fraction of tickets, for the later PII-scrub step to catch
    if rng.random() < 0.04:
        leak_type = rng.choice(["email", "phone"])
        if leak_type == "email":
            text += f" You can reach me directly at {fake.free_email()} if that's easier."
        else:
            text += f" Feel free to call me back at {fake.phone_number()}."
    return text

rng = np.random.default_rng(31)
descriptions = [
    make_description(cat, oid, rng) for cat, oid in zip(categories, all_order_ids)
]

tickets_df = pd.DataFrame({
    "ticket_id": [f"tkt_{200000+i}" for i in range(n_total)],
    "customer_id": all_customer_ids,
    "order_id": all_order_ids,
    "category": categories,
    "priority": priorities,
    "channel": channels,
    "status": status,
    "description": descriptions,
    "opened_at": pd.to_datetime(all_opened).strftime("%Y-%m-%d %H:%M:%S"),
    "resolved_at": resolved_at_final.dt.strftime("%Y-%m-%d %H:%M:%S"),
    "csat_score": csat_scores,
})

tickets_df = tickets_df.sample(frac=1.0, random_state=42).reset_index(drop=True)
tickets_df.to_csv(os.path.join(OUT_DIR, "support_tickets.csv"), index=False)
print(f"support_tickets.csv: {len(tickets_df):,} rows")
pii_count = tickets_df["description"].str.contains("@|call me back", case=False, na=False).sum()
print(f"rows with injected PII-like text: {pii_count:,}")
