with dedup as (
    select
        *,
        row_number() over (partition by customer_id order by updated_at desc) as rn
    from {{ source('bronze', 'customers') }}
)
select
    customer_id,
    first_name,
    last_name,
    lower(trim(email)) as email,
    region,
    city,
    signup_date,
    created_at,
    updated_at
from dedup
where rn = 1
  and customer_id is not null
