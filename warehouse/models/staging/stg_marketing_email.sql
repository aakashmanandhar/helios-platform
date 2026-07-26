with dedup as (
    select
        *,
        row_number() over (partition by send_date, campaign_name order by cost_usd desc) as rn
    from {{ source('bronze', 'marketing_email') }}
)
select
    cast(send_date as date) as spend_date,
    'email' as channel_code,
    campaign_name,
    cost_usd as spend,
    emails_sent,
    opens,
    clicks,
    coalesce(unsubscribes, 0) as unsubscribes
from dedup
where rn = 1
  and send_date is not null
