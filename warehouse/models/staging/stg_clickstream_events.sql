with dedup as (
    select
        *,
        row_number() over (partition by event_id order by event_timestamp) as rn
    from {{ source('bronze', 'clickstream_events') }}
)
select
    event_id,
    session_id,
    customer_id,
    product_id,
    event_type,
    channel,
    cast(event_timestamp as timestamp) as event_timestamp
from dedup
where rn = 1
  and event_id is not null
