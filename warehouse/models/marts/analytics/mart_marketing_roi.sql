with revenue as (
    select
        order_date,
        channel_code,
        sum(total_amount) as revenue,
        count(distinct order_id) as orders
    from {{ ref('fact_orders') }}
    where status = 'completed'
    group by order_date, channel_code
),
spend as (
    select spend_date as order_date, channel_code, total_spend, total_clicks
    from {{ ref('fact_marketing_spend') }}
)
select
    coalesce(r.order_date, s.order_date) as date_day,
    coalesce(r.channel_code, s.channel_code) as channel_code,
    coalesce(r.revenue, 0) as revenue,
    coalesce(r.orders, 0) as orders,
    coalesce(s.total_spend, 0) as spend,
    coalesce(s.total_clicks, 0) as clicks,
    case when coalesce(s.total_spend,0) > 0 then round(coalesce(r.revenue,0) / s.total_spend, 2) else null end as roas,
    case when coalesce(r.orders,0) > 0 then round(coalesce(s.total_spend,0) / r.orders, 2) else null end as cac
from revenue r
full outer join spend s on r.order_date = s.order_date and r.channel_code = s.channel_code
order by date_day, channel_code
