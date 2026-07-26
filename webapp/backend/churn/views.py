"""
Live, low-latency churn scoring: pulls features for a single customer from
Feast's online store (Postgres) and scores them with the trained model.
This is the "real-time churn score available to an API within milliseconds"
piece of the plan - as opposed to batch_score_churn.py, which pre-computes
scores for every customer and writes them into gold for the dashboard/RAG
assistant to read cheaply.
"""
from functools import lru_cache

import joblib
from django.conf import settings
from feast import FeatureStore
from rest_framework.decorators import api_view
from rest_framework.response import Response

from helios_dashboard.bq_client import run_query

FEATURE_COLS = ["recency_days", "frequency", "lifetime_value", "avg_order_value"]


@lru_cache(maxsize=1)
def get_feature_store():
    return FeatureStore(repo_path=str(settings.FEATURE_REPO_PATH))


@lru_cache(maxsize=1)
def get_model_bundle():
    return joblib.load(settings.CHURN_MODEL_PATH)


def _risk_band(prob):
    if prob >= 0.6:
        return "High"
    if prob >= 0.3:
        return "Medium"
    return "Low"


@api_view(["GET"])
def score_customer(request, customer_id):
    store = get_feature_store()
    bundle = get_model_bundle()
    pipeline = bundle["pipeline"]

    features = store.get_online_features(
        features=[f"customer_ltv_rfm_features:{col}" for col in FEATURE_COLS],
        entity_rows=[{"customer_id": int(customer_id)}],
    ).to_dict()

    if features["recency_days"][0] is None:
        return Response(
            {"error": f"No online features found for customer_id={customer_id}"},
            status=404,
        )

    row = [[features[col][0] for col in FEATURE_COLS]]
    probability = float(pipeline.predict_proba(row)[0, 1])

    return Response({
        "customer_id": int(customer_id),
        "features": {col: features[col][0] for col in FEATURE_COLS},
        "churn_probability": round(probability, 4),
        "risk_band": _risk_band(probability),
        "source": "feast_online_store+live_model",
    })


@api_view(["GET"])
def top_risk(request):
    limit = int(request.GET.get("limit", 20))
    rows = run_query(f"""
        SELECT
            customer_id, first_name, last_name, region,
            rfm_segment, churn_probability, risk_band, scored_at
        FROM `gold.mart_churn_predictions`
        ORDER BY churn_probability DESC
        LIMIT {limit}
    """)
    summary = run_query("""
        SELECT risk_band, COUNT(*) AS customer_count
        FROM `gold.mart_churn_predictions`
        GROUP BY risk_band
    """)
    return Response({"top_risk": rows, "summary": summary})
