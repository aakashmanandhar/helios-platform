with dedup as (
    select
        *,
        row_number() over (partition by payment_id order by created_at) as rn
    from {{ source('bronze', 'payments') }}
)
select
    payment_id,
    order_id,
    amount,
    currency,
    status,
    payment_method,
    processor_fee,
    refunded_amount,
    cast(created_at as timestamp) as created_at
from dedup
where rn = 1
  and payment_id is not null
