{% if target.type == 'bigquery' %}
with date_spine as (
    select date_day
    from unnest(generate_date_array('2023-01-01', '2026-12-31', interval 1 day)) as date_day
)
select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(quarter from date_day) as quarter,
    extract(dayofweek from date_day) - 1 as day_of_week,
    format_date('%A', date_day) as day_name,
    format_date('%B', date_day) as month_name,
    case when extract(dayofweek from date_day) in (1, 7) then true else false end as is_weekend,
    case when extract(month from date_day) in (11, 12) then true else false end as is_holiday_season
from date_spine
{% else %}
with date_spine as (
    select cast(generate_series as date) as date_day
    from generate_series(timestamp '2023-01-01', timestamp '2026-12-31', interval 1 day)
)
select
    date_day,
    extract(year from date_day)::int as year,
    extract(month from date_day)::int as month,
    extract(day from date_day)::int as day,
    extract(quarter from date_day)::int as quarter,
    extract(dow from date_day)::int as day_of_week,
    strftime(date_day, '%A') as day_name,
    strftime(date_day, '%B') as month_name,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend,
    case when extract(month from date_day) in (11, 12) then true else false end as is_holiday_season
from date_spine
{% endif %}
