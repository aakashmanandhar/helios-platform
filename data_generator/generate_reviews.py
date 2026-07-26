import os
import numpy as np
import pandas as pd
from db import get_connection

np.random.seed(47)
rng = np.random.default_rng(47)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "reviews")
os.makedirs(OUT_DIR, exist_ok=True)

conn = get_connection()
completed_items = pd.read_sql("""
    SELECT oi.order_item_id, oi.order_id, oi.product_id, o.customer_id, o.order_date
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
""", conn)
products = pd.read_sql("SELECT product_id, product_name FROM products ORDER BY product_id", conn)
customers = pd.read_sql("SELECT customer_id FROM customers ORDER BY customer_id", conn)
conn.close()

product_name_map = dict(zip(products["product_id"], products["product_name"]))

# --- Verified-purchase reviews: ~10% of completed order line items get reviewed ---
review_mask = rng.random(len(completed_items)) < 0.10
verified = completed_items[review_mask].copy()
verified["verified_purchase"] = True
verified["review_date"] = pd.to_datetime(verified["order_date"]) + pd.to_timedelta(
    rng.integers(3, 60, size=len(verified)), unit="D"
)

# --- Unverified reviews: not tied to one of our completed orders (gift, bought elsewhere, etc.) ---
n_unverified = 40000
all_product_ids = products["product_id"].values
all_customer_ids = customers["customer_id"].values
START = pd.Timestamp("2024-07-20")
N_DAYS = 730
unverified = pd.DataFrame({
    "product_id": rng.choice(all_product_ids, size=n_unverified),
    "customer_id": rng.choice(all_customer_ids, size=n_unverified),
    "order_id": np.nan,
    "verified_purchase": False,
    "review_date": START + pd.to_timedelta(rng.integers(0, N_DAYS, size=n_unverified), unit="D"),
})

reviews_df = pd.concat([
    verified[["order_id", "product_id", "customer_id", "review_date", "verified_purchase"]],
    unverified[["order_id", "product_id", "customer_id", "review_date", "verified_purchase"]],
], ignore_index=True)

n_total = len(reviews_df)
ratings = rng.choice([1, 2, 3, 4, 5], size=n_total, p=[0.10, 0.05, 0.10, 0.20, 0.55])

TEMPLATES = {
    "negative": [
        "Really disappointed with the {product}. Broke down within a week and support was slow to respond.",
        "Not worth the money. The {product} feels cheaply made compared to the photos.",
        "Would not recommend the {product}. Arrived with defects and didn't match the listing.",
        "The {product} stopped working almost immediately. Returning this one.",
    ],
    "neutral": [
        "The {product} is okay for the price, does the job but nothing special.",
        "Mixed feelings about the {product} - some features are great, others feel unfinished.",
        "The {product} works as described but shipping took longer than expected.",
        "Average experience with the {product}. Might look elsewhere next time.",
    ],
    "positive": [
        "Love the {product}! Exactly what I was looking for and arrived quickly.",
        "The {product} exceeded my expectations, great build quality for the price.",
        "Highly recommend the {product}, works perfectly and looks even better in person.",
        "Best purchase in a while - the {product} has been reliable every day since I got it.",
    ],
}

def sentiment_bucket(rating):
    if rating <= 2:
        return "negative"
    if rating == 3:
        return "neutral"
    return "positive"

def make_review_text(product_id, rating, r):
    # ~15% of reviews are rating-only, no text - realistic on real platforms
    if r.random() < 0.15:
        return None
    bucket = sentiment_bucket(rating)
    template = r.choice(TEMPLATES[bucket])
    product = product_name_map.get(product_id, "product")
    return template.format(product=product)

review_texts = [
    make_review_text(pid, rating, rng) for pid, rating in zip(reviews_df["product_id"], ratings)
]

reviews_df["rating"] = ratings
reviews_df["review_text"] = review_texts
reviews_df["helpful_votes"] = rng.poisson(lam=np.where(ratings >= 4, 2.5, 1.2), size=n_total)
reviews_df["review_date"] = pd.to_datetime(reviews_df["review_date"]).dt.strftime("%Y-%m-%d")
reviews_df["review_id"] = [f"rev_{500000+i}" for i in range(n_total)]

# deliberate messiness: ~2% duplicate submissions (accidental double-post of the same review)
dup_frac = 0.02
n_dupes = int(n_total * dup_frac)
dupe_rows = reviews_df.sample(n=n_dupes, random_state=7).copy()
dupe_rows["review_id"] = [f"rev_{900000+i}" for i in range(n_dupes)]
reviews_df = pd.concat([reviews_df, dupe_rows], ignore_index=True)

reviews_df = reviews_df[[
    "review_id", "product_id", "customer_id", "order_id", "rating",
    "review_text", "verified_purchase", "helpful_votes", "review_date"
]]
reviews_df = reviews_df.sample(frac=1.0, random_state=99).reset_index(drop=True)
reviews_df.to_csv(os.path.join(OUT_DIR, "product_reviews.csv"), index=False)

print(f"product_reviews.csv: {len(reviews_df):,} rows")
print(f"verified: {int(reviews_df['verified_purchase'].sum()):,}, unverified: {int((~reviews_df['verified_purchase']).sum()):,}")
print(f"null review_text (rating-only): {reviews_df['review_text'].isna().sum():,}")
print(f"duplicate review_ids injected: {n_dupes:,}")
