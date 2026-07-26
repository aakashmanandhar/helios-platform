with dedup as (
    select
        *,
        row_number() over (partition by ticket_id order by opened_at) as rn
    from {{ source('bronze', 'support_tickets') }}
)
select
    ticket_id,
    customer_id,
    order_id,
    category,
    priority,
    channel,
    status,
    cast(opened_at as timestamp) as opened_at,
    cast(resolved_at as timestamp) as resolved_at,
    csat_score
from dedup
where rn = 1
  and ticket_id is not null
