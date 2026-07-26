from datetime import timedelta
from feast import Entity, FeatureView, Field, FileSource
from feast.types import Int64, Float32

customer = Entity(name="customer_id", join_keys=["customer_id"])

customer_source = FileSource(
    path="data/customer_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp",
)

customer_features_view = FeatureView(
    name="customer_ltv_rfm_features",
    entities=[customer],
    ttl=timedelta(days=3650),
    schema=[
        Field(name="recency_days", dtype=Int64),
        Field(name="frequency", dtype=Int64),
        Field(name="lifetime_value", dtype=Float32),
        Field(name="avg_order_value", dtype=Float32),
        Field(name="r_score", dtype=Int64),
        Field(name="f_score", dtype=Int64),
        Field(name="m_score", dtype=Int64),
        Field(name="rfm_total", dtype=Int64),
        Field(name="churned", dtype=Int64),
    ],
    source=customer_source,
    online=True,
)
