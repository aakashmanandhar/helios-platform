select
    o.order_id,
    o.customer_id,
    cast(o.order_date as date) as order_date,
    o.channel as channel_code,
    o.status,
    o.subtotal,
    o.discount,
    o.shipping_fee,
    o.tax,
    o.total_amount
from {{ ref('stg_orders') }} o
