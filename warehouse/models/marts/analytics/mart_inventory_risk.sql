select
    i.product_id,
    p.product_name,
    p.category,
    p.brand,
    i.warehouse_code,
    w.warehouse_name,
    w.region,
    i.stock_qty,
    i.reorder_point,
    i.is_stockout,
    i.is_overstock,
    case
        when i.is_stockout then 'Stockout'
        when i.stock_qty <= i.reorder_point then 'Reorder Needed'
        when i.is_overstock then 'Overstocked'
        else 'Healthy'
    end as inventory_status,
    round(i.stock_qty * p.unit_cost, 2) as inventory_value_at_cost
from {{ ref('fact_inventory_snapshot') }} i
join {{ ref('dim_product') }} p on i.product_id = p.product_id
join {{ ref('dim_warehouse') }} w on i.warehouse_code = w.warehouse_code
