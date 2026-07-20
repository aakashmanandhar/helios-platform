select
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    unit_price,
    unit_cost,
    round(unit_price - unit_cost, 2) as unit_margin
from {{ ref('stg_products') }}
