with source as (

    select * from {{ source('ecb', 'ecb_exchange_rates') }}

)

select
    currency::text  as currency_code,
    rate_date,
    rate            as eur_rate,
    _batch_id       as batch_id,
    _loaded_at      as loaded_at
from source
