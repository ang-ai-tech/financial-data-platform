with source as (

    select * from {{ source('fred', 'fred_series') }}

)

select
    series_id,
    series_name,
    units,
    frequency,
    category
from source
