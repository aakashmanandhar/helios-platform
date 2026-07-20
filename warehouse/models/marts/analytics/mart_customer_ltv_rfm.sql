with customer_orders as (
    select
        customer_id,
        count(*) as frequency,
        sum(total_amount) as monetary,
        max(order_date) as last_order_date,
        min(order_date) as first_order_date
    from {{ ref('fact_orders') }}
    where status = 'completed'
    group by 1
),

recency_calc as (
    select
        *,
        date_diff('day', last_order_date, current_date) as recency_days,
        date_diff('day', first_order_date, current_date) as tenure_days
    from customer_orders
),

scored as (
    select
        *,
        ntile(5) over (order by recency_days desc) as r_score,
        ntile(5) over (order by frequency asc) as f_score,
        ntile(5) over (order by monetary asc) as m_score
    from recency_calc
),

segmented as (
    select
        *,
        (r_score + f_score + m_score) as rfm_total,
        case
            when r_score >= 4 and f_score >= 4 then 'Champions'
            when r_score >= 3 and f_score >= 3 then 'Loyal Customers'
            when r_score >= 4 and f_score <= 2 then 'New Customers'
            when r_score <= 2 and f_score >= 3 then 'At Risk'
            when r_score <= 2 and f_score <= 2 then 'Lost'
            else 'Needs Attention'
        end as rfm_segment
    from scored
)

select
    s.customer_id,
    c.first_name,
    c.last_name,
    c.region,
    s.frequency,
    round(s.monetary, 2) as lifetime_value,
    round(s.monetary / nullif(s.frequency, 0), 2) as avg_order_value,
    s.first_order_date,
    s.last_order_date,
    s.recency_days,
    s.tenure_days,
    s.r_score,
    s.f_score,
    s.m_score,
    s.rfm_total,
    s.rfm_segment
from segmented s
join {{ ref('dim_customer') }} c on s.customer_id = c.customer_id
