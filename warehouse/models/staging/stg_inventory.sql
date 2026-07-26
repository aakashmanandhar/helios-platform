with dedup as (
    select
        *,
        row_number() over (partition by product_id, warehouse_code order by last_updated desc) as rn
    from {{ source('bronze', 'inventory') }}
)
select
    inventory_id,
    product_id,
    warehouse_code,
    stock_qty,
    reorder_point,
    {% if target.type == 'bigquery' %}
    timestamp_micros(div(last_updated, 1000)) as last_updated
    {% else %}
    last_updated
    {% endif %}
from dedup
where rn = 1
