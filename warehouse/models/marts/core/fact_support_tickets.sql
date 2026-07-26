select
    ticket_id,
    customer_id,
    order_id,
    category,
    priority,
    channel,
    status,
    cast(opened_at as date) as opened_date,
    opened_at,
    resolved_at,
    date_diff('hour', opened_at, resolved_at) as resolution_hours,
    csat_score
from {{ ref('stg_support_tickets') }}
