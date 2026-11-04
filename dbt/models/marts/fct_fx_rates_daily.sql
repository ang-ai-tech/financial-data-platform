select
    currency_code,
    rate_date,
    eur_rate,
    previous_eur_rate,
    daily_return,
    volatility_20d_annualised
from {{ ref('int_fx_rates__returns') }}
