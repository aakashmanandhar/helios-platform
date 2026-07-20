select
    customer_id,
    first_name,
    last_name,
    email,
    region,
    city,
    signup_date
from {{ ref('stg_customers') }}
