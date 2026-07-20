select
    product_id,
    warehouse_code,
    stock_qty,
    reorder_point,
    cast(last_updated as date) as snapshot_date,
    case when stock_qty = 0 then true else false end as is_stockout,
    case when stock_qty > reorder_point * 5 then true else false end as is_overstock
from {{ ref('stg_inventory') }}
