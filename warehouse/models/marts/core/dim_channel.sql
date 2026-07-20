select channel_code, channel_name, channel_type
from {{ ref('channel_seed') }}
