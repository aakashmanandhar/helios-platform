with dedup as (
    select
        *,
        row_number() over (partition by order_id order by updated_at desc) as rn
    from {{ source('bronze', 'orders') }}
)
select
    order_id,
    customer_id,
    order_date,
    status,
    channel,
    subtotal,
    discount,
    shipping_fee,
    tax,
    total_amount,
    created_at,
    updated_at
from dedup
where rn = 1
  and order_id is not null
  and total_amount >= 0
