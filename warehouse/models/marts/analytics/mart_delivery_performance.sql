select
    carrier,
    warehouse_code,
    count(*) as total_shipments,
    sum(case when status = 'delivered' then 1 else 0 end) as delivered_count,
    sum(case when status = 'exception' then 1 else 0 end) as exception_count,
    sum(case when is_late then 1 else 0 end) as late_count,
    round(100.0 * sum(case when is_late then 1 else 0 end) / nullif(sum(case when status = 'delivered' then 1 else 0 end), 0), 2) as late_pct,
    round(100.0 * sum(case when status = 'exception' then 1 else 0 end) / count(*), 2) as exception_pct,
    round(avg(estimated_transit_days), 2) as avg_estimated_transit_days
from {{ ref('fact_shipments') }}
group by carrier, warehouse_code
order by carrier, warehouse_code
