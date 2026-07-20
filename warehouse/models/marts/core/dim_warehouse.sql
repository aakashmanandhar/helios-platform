select warehouse_code, warehouse_name, region
from {{ ref('warehouse_seed') }}
