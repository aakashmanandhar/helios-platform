with dedup as (
    select
        *,
        row_number() over (partition by date, campaign_id order by cost_usd desc nulls last) as rn
    from {{ source('bronze', 'marketing_google') }}
)
select
    cast(date as date) as spend_date,
    'paid_search' as channel_code,
    campaign_name,
    coalesce(cost_usd, 0) as spend,
    impressions,
    clicks
from dedup
where rn = 1
  and date is not null
  and (cost_usd is null or cost_usd >= 0)
