import os
import random
import numpy as np
import pandas as pd

np.random.seed(11)
random.seed(11)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "external_feeds", "marketing")
os.makedirs(OUT_DIR, exist_ok=True)

START = pd.Timestamp("2024-07-20")
N_DAYS = 730
dates = START + pd.to_timedelta(np.arange(N_DAYS), unit="D")

# ---------- Google Ads: date, campaign_id, campaign_name, impressions, clicks, cost_usd ----------
GOOGLE_CAMPAIGNS = [
    (101, "Brand - Search"), (102, "Generic - Search"), (103, "Shopping - All Products"),
    (104, "Retargeting - Display"), (105, "YouTube - Awareness"), (106, "Competitor - Search"),
]
rows = []
for cid, cname in GOOGLE_CAMPAIGNS:
    base_daily_cost = np.random.uniform(200, 1500)
    for d in dates:
        month_mult = 1.6 if d.month in (11, 12) else (0.8 if d.month in (1, 2) else 1.0)
        cost = base_daily_cost * month_mult * np.random.uniform(0.7, 1.3)
        impressions = int(cost * np.random.uniform(80, 150))
        clicks = int(impressions * np.random.uniform(0.02, 0.06))
        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "campaign_id": cid,
            "campaign_name": cname,
            "impressions": impressions,
            "clicks": clicks,
            "cost_usd": round(cost, 2),
        })
google_df = pd.DataFrame(rows)
missing_idx = google_df.sample(frac=0.01, random_state=1).index
google_df.loc[missing_idx, "cost_usd"] = None
credit_idx = google_df.sample(frac=0.003, random_state=2).index
google_df.loc[credit_idx, "cost_usd"] = -abs(google_df.loc[credit_idx, "cost_usd"].fillna(10)) * 0.1
dup_rows = google_df.sample(frac=0.005, random_state=3)
google_df = pd.concat([google_df, dup_rows], ignore_index=True)
google_df.to_csv(os.path.join(OUT_DIR, "google_ads_daily.csv"), index=False)
print(f"google_ads_daily.csv: {len(google_df):,} rows")

# ---------- Meta Ads: report_date (MM/DD/YYYY), ad_set_id, ad_set_name, spend, impressions, clicks ----------
META_ADSETS = [
    (201, "Prospecting - Broad"), (202, "Retargeting - Cart Abandoners"),
    (203, "Lookalike - Top Customers"), (204, "Prospecting - Interests"), (205, "Retargeting - Viewed Product"),
]
rows = []
for aid, aname in META_ADSETS:
    base_daily_spend = np.random.uniform(150, 1200)
    for d in dates:
        month_mult = 1.5 if d.month in (11, 12) else (0.85 if d.month in (1, 2) else 1.0)
        spend = base_daily_spend * month_mult * np.random.uniform(0.7, 1.3)
        impressions = int(spend * np.random.uniform(100, 200))
        clicks = int(impressions * np.random.uniform(0.01, 0.04))
        rows.append({
            "report_date": d.strftime("%m/%d/%Y"),
            "ad_set_id": aid,
            "ad_set_name": aname,
            "spend": round(spend, 2),
            "impressions": impressions,
            "clicks": clicks,
        })
meta_df = pd.DataFrame(rows)
missing_idx = meta_df.sample(frac=0.015, random_state=4).index
meta_df.loc[missing_idx, "impressions"] = None
dup_rows = meta_df.sample(frac=0.004, random_state=5)
meta_df = pd.concat([meta_df, dup_rows], ignore_index=True)
meta_df.to_csv(os.path.join(OUT_DIR, "meta_ads_daily.csv"), index=False)
print(f"meta_ads_daily.csv: {len(meta_df):,} rows")

# ---------- Email/ESP: campaign-send grain (not daily), ISO datetime ----------
EMAIL_CAMPAIGN_TYPES = ["Weekly Newsletter", "Flash Sale", "Abandoned Cart", "Win-back", "New Arrivals", "Holiday Promo"]
n_campaigns = 260
send_days = np.sort(np.random.choice(N_DAYS, size=n_campaigns, replace=False))
rows = []
for i, day_offset in enumerate(send_days):
    send_ts = START + pd.Timedelta(days=int(day_offset), hours=random.choice([8, 10, 14, 18]))
    campaign_name = random.choice(EMAIL_CAMPAIGN_TYPES)
    emails_sent = int(np.random.uniform(20000, 180000))
    open_rate = np.random.uniform(0.15, 0.35)
    click_rate = np.random.uniform(0.02, 0.08)
    opens = int(emails_sent * open_rate)
    clicks = int(opens * click_rate)
    unsubscribes = int(emails_sent * np.random.uniform(0.0005, 0.003))
    cost = round(emails_sent * np.random.uniform(0.001, 0.004), 2)
    rows.append({
        "send_date": send_ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "campaign_name": f"{campaign_name} #{i+1}",
        "emails_sent": emails_sent,
        "opens": opens,
        "clicks": clicks,
        "unsubscribes": unsubscribes,
        "cost_usd": cost,
    })
email_df = pd.DataFrame(rows)
missing_idx = email_df.sample(frac=0.02, random_state=6).index
email_df.loc[missing_idx, "unsubscribes"] = None
email_df.to_csv(os.path.join(OUT_DIR, "email_campaign_sends.csv"), index=False)
print(f"email_campaign_sends.csv: {len(email_df):,} rows")

print("Marketing feed generation complete.")
