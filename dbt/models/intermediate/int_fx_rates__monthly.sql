select
    currency_code,
    date_trunc('month', rate_date)::date                    as month_start,
    avg(eur_rate)                                           as avg_eur_rate,
    (array_agg(eur_rate order by rate_date desc))[1]        as month_end_eur_rate,
    min(eur_rate)                                           as min_eur_rate,
    max(eur_rate)                                           as max_eur_rate,
    count(*)                                                as business_days
from {{ ref('stg_ecb__exchange_rates') }}
group by 1, 2
