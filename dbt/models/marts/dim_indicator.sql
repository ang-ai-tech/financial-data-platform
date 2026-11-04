select
    series_id,
    series_name,
    units,
    frequency,
    category
from {{ ref('stg_fred__series') }}
