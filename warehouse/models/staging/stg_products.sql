with dedup as (
    select
        *,
        row_number() over (partition by product_id order by updated_at desc) as rn
    from {{ source('bronze', 'products') }}
)
select
    product_id,
    product_name,
    category,
    subcategory,
    brand,
    unit_price,
    unit_cost,
    created_at,
    updated_at
from dedup
where rn = 1
  and product_id is not null
  and unit_price >= 0
