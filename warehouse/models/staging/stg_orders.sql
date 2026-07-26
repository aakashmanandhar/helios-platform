with dedup as (
    select
        *,
        row_number() over (partition by order_id order by updated_at desc) as rn
    from {{ source('bronze', 'orders') }}
)
select
    order_id,
    customer_id,
    {% if target.type == 'bigquery' %}
    timestamp_micros(div(order_date, 1000)) as order_date,
    {% else %}
    order_date,
    {% endif %}
    status,
    channel,
    subtotal,
    discount,
    shipping_fee,
    tax,
    total_amount,
    {% if target.type == 'bigquery' %}
    timestamp_micros(div(created_at, 1000)) as created_at,
    timestamp_micros(div(updated_at, 1000)) as updated_at
    {% else %}
    created_at,
    updated_at
    {% endif %}
from dedup
where rn = 1
  and order_id is not null
  and total_amount >= 0
