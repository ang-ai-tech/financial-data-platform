select
    currency_code,
    currency_name,
    region
from {{ ref('currencies') }}
