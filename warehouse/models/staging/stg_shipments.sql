with dedup as (
    select
        *,
        row_number() over (partition by shipment_id order by ship_date) as rn
    from {{ source('bronze', 'shipments') }}
)
select
    shipment_id,
    order_id,
    carrier,
    origin_warehouse,
    cast(ship_date as date) as ship_date,
    cast(estimated_delivery_date as date) as estimated_delivery_date,
    cast(actual_delivery_date as date) as actual_delivery_date,
    status
from dedup
where rn = 1
  and shipment_id is not null
