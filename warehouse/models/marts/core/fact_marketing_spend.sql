with google as (
    select spend_date, channel_code, spend, impressions, clicks from {{ ref('stg_marketing_google') }}
),
meta as (
    select spend_date, channel_code, spend, impressions, clicks from {{ ref('stg_marketing_meta') }}
),
email as (
    select spend_date, channel_code, spend, cast(null as bigint) as impressions, clicks from {{ ref('stg_marketing_email') }}
),
unioned as (
    select * from google
    union all
    select * from meta
    union all
    select * from email
)
select
    spend_date,
    channel_code,
    round(sum(spend), 2) as total_spend,
    sum(impressions) as total_impressions,
    sum(clicks) as total_clicks
from unioned
group by spend_date, channel_code
