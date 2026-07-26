select
    shipment_id,
    order_id,
    carrier,
    origin_warehouse as warehouse_code,
    ship_date,
    estimated_delivery_date,
    actual_delivery_date,
    status,
    date_diff('day', ship_date, estimated_delivery_date) as estimated_transit_days,
    date_diff('day', estimated_delivery_date, actual_delivery_date) as days_late,
    case when actual_delivery_date > estimated_delivery_date then true else false end as is_late
from {{ ref('stg_shipments') }}
