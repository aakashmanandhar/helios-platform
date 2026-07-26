import os
import time
import requests
import pandas as pd
from datetime import date, datetime, timezone

CITIES = {
    "NE": {"name": "New York, NY", "lat": 40.7128, "lon": -74.0060},
    "SE": {"name": "Atlanta, GA", "lat": 33.7490, "lon": -84.3880},
    "MW": {"name": "Chicago, IL", "lat": 41.8781, "lon": -87.6298},
    "SW": {"name": "Dallas, TX", "lat": 32.7767, "lon": -96.7970},
    "WC": {"name": "Los Angeles, CA", "lat": 34.0522, "lon": -118.2437},
}

HEADERS = {"User-Agent": "helios-platform-demo (aakashmanandhar@gmail.com)"}
INGEST_DATE = date.today().isoformat()
BRONZE_ROOT = os.path.join(os.path.dirname(__file__), "..", "lake", "bronze", "weather_daily")

rows = []
for region_code, info in CITIES.items():
    lat, lon = info["lat"], info["lon"]
    points_resp = requests.get(f"https://api.weather.gov/points/{lat},{lon}", headers=HEADERS, timeout=15)
    points_resp.raise_for_status()
    forecast_url = points_resp.json()["properties"]["forecast"]
    time.sleep(1)

    forecast_resp = requests.get(forecast_url, headers=HEADERS, timeout=15)
    forecast_resp.raise_for_status()
    today_period = forecast_resp.json()["properties"]["periods"][0]

    rows.append({
        "region_code": region_code,
        "city_name": info["name"],
        "forecast_date": date.today().isoformat(),
        "period_name": today_period["name"],
        "temperature": today_period["temperature"],
        "temperature_unit": today_period["temperatureUnit"],
        "wind_speed": today_period["windSpeed"],
        "wind_direction": today_period["windDirection"],
        "short_forecast": today_period["shortForecast"],
        "detailed_forecast": today_period["detailedForecast"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    })
    time.sleep(1)

weather_df = pd.DataFrame(rows)
out_dir = os.path.join(BRONZE_ROOT, f"ingested_date={INGEST_DATE}")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "part-0.parquet")
weather_df.to_parquet(out_path, index=False)
print(weather_df[["region_code", "city_name", "temperature", "temperature_unit", "short_forecast"]])
print(f"Weather data landed -> {out_path}")
