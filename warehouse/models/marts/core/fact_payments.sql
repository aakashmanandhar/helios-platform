select
    payment_id,
    order_id,
    cast(created_at as date) as payment_date,
    amount,
    status,
    payment_method,
    processor_fee,
    refunded_amount,
    created_at
from {{ ref('stg_payments') }}
