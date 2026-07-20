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
    last_updated
from dedup
where rn = 1
