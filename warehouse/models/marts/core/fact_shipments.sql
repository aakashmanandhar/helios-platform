select
    shipment_id,
    order_id,
    carrier,
    origin_warehouse as warehouse_code,
    ship_date,
    estimated_delivery_date,
    actual_delivery_date,
    status,
    {% if target.type == 'bigquery' %}
    date_diff(estimated_delivery_date, ship_date, day) as estimated_transit_days,
    date_diff(actual_delivery_date, estimated_delivery_date, day) as days_late,
    {% else %}
    date_diff('day', ship_date, estimated_delivery_date) as estimated_transit_days,
    date_diff('day', estimated_delivery_date, actual_delivery_date) as days_late,
    {% endif %}
    case when actual_delivery_date > estimated_delivery_date then true else false end as is_late
from {{ ref('stg_shipments') }}
