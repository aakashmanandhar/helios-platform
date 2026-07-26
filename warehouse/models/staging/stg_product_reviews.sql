with dedup as (
    select
        *,
        row_number() over (partition by review_id order by review_date) as rn
    from {{ source('bronze', 'product_reviews') }}
)
select
    review_id,
    product_id,
    customer_id,
    order_id,
    rating,
    review_text,
    verified_purchase,
    coalesce(helpful_votes, 0) as helpful_votes,
    cast(review_date as date) as review_date
from dedup
where rn = 1
  and review_id is not null
  and rating between 1 and 5
