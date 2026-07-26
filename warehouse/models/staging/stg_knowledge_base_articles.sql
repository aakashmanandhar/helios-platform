select
    doc_id,
    doc_name,
    title,
    content,
    category,
    cast(last_updated as timestamp) as last_updated
from {{ source('bronze', 'knowledge_base_articles') }}
where doc_id is not null
