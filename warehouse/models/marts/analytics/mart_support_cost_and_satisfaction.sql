select
    category,
    priority,
    count(*) as ticket_count,
    round(avg(resolution_hours), 1) as avg_resolution_hours,
    round(avg(csat_score), 2) as avg_csat_score,
    sum(case when csat_score is not null then 1 else 0 end) as csat_responses
from {{ ref('fact_support_tickets') }}
group by category, priority
order by category, priority
