select
    review_id,
    product_id,
    customer_id,
    order_id,
    rating,
    review_text,
    case when review_text is not null then true else false end as has_text,
    verified_purchase,
    helpful_votes,
    review_date
from {{ ref('stg_product_reviews') }}
