with session_funnel as (
    select
        session_id,
        channel_code,
        min(event_date) as session_date,
        max(case when event_type = 'page_view' then 1 else 0 end) as viewed,
        max(case when event_type = 'add_to_cart' then 1 else 0 end) as carted,
        max(case when event_type = 'checkout_start' then 1 else 0 end) as checked_out,
        max(case when event_type = 'purchase' then 1 else 0 end) as purchased
    from {{ ref('fact_events') }}
    group by session_id, channel_code
)
select
    session_date,
    channel_code,
    count(*) as sessions,
    sum(viewed) as viewed_sessions,
    sum(carted) as carted_sessions,
    sum(checked_out) as checkout_sessions,
    sum(purchased) as purchase_sessions,
    round(100.0 * sum(carted) / nullif(sum(viewed), 0), 2) as view_to_cart_pct,
    round(100.0 * sum(checked_out) / nullif(sum(carted), 0), 2) as cart_to_checkout_pct,
    round(100.0 * sum(purchased) / nullif(sum(checked_out), 0), 2) as checkout_to_purchase_pct,
    round(100.0 * sum(purchased) / nullif(sum(viewed), 0), 2) as overall_conversion_pct
from session_funnel
group by session_date, channel_code
order by session_date, channel_code
