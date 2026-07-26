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
    {% if target.type == 'bigquery' %}
    timestamp_diff(resolved_at, opened_at, hour) as resolution_hours,
    {% else %}
    date_diff('hour', opened_at, resolved_at) as resolution_hours,
    {% endif %}
    csat_score
from {{ ref('stg_support_tickets') }}
