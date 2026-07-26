select
    e.event_id,
    e.session_id,
    e.customer_id,
    e.product_id,
    e.event_type,
    e.channel as channel_code,
    cast(e.event_timestamp as date) as event_date,
    e.event_timestamp
from {{ ref('stg_clickstream_events') }} e
