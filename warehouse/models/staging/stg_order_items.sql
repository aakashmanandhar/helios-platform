with dedup as (
    select
        *,
        row_number() over (partition by order_item_id order by order_item_id) as rn
    from {{ source('bronze', 'order_items') }}
)
select
    order_item_id,
    order_id,
    product_id,
    quantity,
    unit_price,
    line_total
from dedup
where rn = 1
  and quantity > 0
  and unit_price >= 0
