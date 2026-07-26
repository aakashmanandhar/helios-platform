import io
import os
import random
import numpy as np
import pandas as pd
from faker import Faker
from db import get_connection

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

N_CUSTOMERS = int(os.getenv("N_CUSTOMERS", "200000"))
N_PRODUCTS = int(os.getenv("N_PRODUCTS", "8000"))

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
CITIES_BY_REGION = {
    "Northeast": ["New York", "Boston", "Philadelphia", "Pittsburgh"],
    "Southeast": ["Atlanta", "Miami", "Charlotte", "Nashville"],
    "Midwest": ["Chicago", "Detroit", "Columbus", "Minneapolis"],
    "Southwest": ["Dallas", "Houston", "Phoenix", "Austin"],
    "West": ["Los Angeles", "San Francisco", "Seattle", "Denver"],
}

def gen_customers(n):
    first_names = [fake.first_name() for _ in range(n)]
    last_names = [fake.last_name() for _ in range(n)]
    regions = np.random.choice(REGIONS, size=n)
    cities = [random.choice(CITIES_BY_REGION[r]) for r in regions]
    emails = [f"{fn.lower()}.{ln.lower()}{i}@example.com" for i, (fn, ln) in enumerate(zip(first_names, last_names))]
    days_back = np.random.exponential(scale=365, size=n).astype(int)
    days_back = np.clip(days_back, 0, 1095)
    signup_dates = pd.Timestamp("2026-07-20") - pd.to_timedelta(days_back, unit="D")

    return pd.DataFrame({
        "first_name": first_names,
        "last_name": last_names,
        "email": emails,
        "region": regions,
        "city": cities,
        "signup_date": signup_dates.date,
    })

CATEGORY_TAXONOMY = {
    "Electronics": ["Headphones", "Laptops", "Smartphones", "Cameras", "Speakers", "Monitors", "Keyboards", "Mice", "Televisions", "Tablets"],
    "Home & Kitchen": ["Cookware", "Blenders", "Coffee Makers", "Vacuum Cleaners", "Bedding", "Furniture", "Lighting", "Storage"],
    "Apparel": ["Mens Shirts", "Womens Dresses", "Jackets", "Shoes", "Activewear", "Accessories", "Jeans"],
    "Beauty": ["Skincare", "Haircare", "Makeup", "Fragrance"],
    "Sports & Outdoors": ["Fitness Equipment", "Camping Gear", "Cycling", "Team Sports"],
    "Toys & Games": ["Board Games", "Action Figures", "Puzzles", "Outdoor Toys"],
    "Books & Media": ["Fiction", "Non-Fiction", "Childrens Books"],
    "Grocery": ["Snacks", "Beverages", "Pantry Staples"],
}
DESCRIPTORS = ["Pro", "Ultra", "Classic", "Essential", "Premium", "Compact", "Deluxe", "Everyday", "Advanced", "Signature"]
PRICE_RANGES = {
    "Electronics": (30, 1200), "Home & Kitchen": (15, 400), "Apparel": (10, 150),
    "Beauty": (5, 80), "Sports & Outdoors": (10, 500), "Toys & Games": (5, 100),
    "Books & Media": (5, 40), "Grocery": (2, 30),
}

def gen_products(n):
    brands = [fake.company().split(",")[0].split(" ")[0] for _ in range(150)]
    categories = list(CATEGORY_TAXONOMY.keys())
    rows = []
    for _ in range(n):
        cat = random.choice(categories)
        subcat = random.choice(CATEGORY_TAXONOMY[cat])
        brand = random.choice(brands)
        descriptor = random.choice(DESCRIPTORS)
        name = f"{brand} {descriptor} {subcat}"
        low, high = PRICE_RANGES[cat]
        price = round(random.uniform(low, high), 2)
        margin = random.uniform(0.35, 0.65)
        cost = round(price * (1 - margin), 2)
        rows.append((name, cat, subcat, brand, price, cost))
    return pd.DataFrame(rows, columns=["product_name", "category", "subcategory", "brand", "unit_price", "unit_cost"])

def copy_df(conn, df, table, columns):
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=False, columns=columns)
    buf.seek(0)
    with conn.cursor() as cur:
        cur.copy_expert(f"COPY {table} ({', '.join(columns)}) FROM STDIN WITH (FORMAT csv)", buf)
    conn.commit()

if __name__ == "__main__":
    conn = get_connection()

    print(f"Generating {N_CUSTOMERS:,} customers...")
    customers_df = gen_customers(N_CUSTOMERS)
    copy_df(conn, customers_df, "customers", ["first_name", "last_name", "email", "region", "city", "signup_date"])
    print("Customers loaded.")

    print(f"Generating {N_PRODUCTS:,} products...")
    products_df = gen_products(N_PRODUCTS)
    copy_df(conn, products_df, "products", ["product_name", "category", "subcategory", "brand", "unit_price", "unit_cost"])
    print("Products loaded.")

    conn.close()
    print("Done.")
