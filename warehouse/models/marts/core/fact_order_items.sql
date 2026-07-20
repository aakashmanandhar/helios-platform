select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    o.customer_id,
    cast(o.order_date as date) as order_date,
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    round(oi.line_total - (p.unit_cost * oi.quantity), 2) as line_margin
from {{ ref('stg_order_items') }} oi
join {{ ref('stg_orders') }} o on oi.order_id = o.order_id
join {{ ref('stg_products') }} p on oi.product_id = p.product_id
