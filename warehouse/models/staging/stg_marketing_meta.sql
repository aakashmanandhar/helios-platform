with dedup as (
    select
        *,
        row_number() over (partition by report_date, ad_set_id order by spend desc) as rn
    from {{ source('bronze', 'marketing_meta') }}
)
select
    {% if target.type == 'bigquery' %}
    parse_date('%m/%d/%Y', report_date) as spend_date,
    {% else %}
    strptime(report_date, '%m/%d/%Y')::date as spend_date,
    {% endif %}
    'paid_social' as channel_code,
    ad_set_name as campaign_name,
    spend,
    coalesce(impressions, 0) as impressions,
    clicks
from dedup
where rn = 1
  and report_date is not null
