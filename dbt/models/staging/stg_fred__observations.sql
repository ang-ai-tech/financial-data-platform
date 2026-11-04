with source as (

    select * from {{ source('fred', 'fred_observations') }}

)

select
    series_id,
    observation_date,
    value,
    _batch_id   as batch_id,
    _loaded_at  as loaded_at
from source
