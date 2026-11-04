{#
    Daily returns and rolling volatility per currency.
    eur_rate is "currency per 1 EUR": a positive return means the euro appreciated.
#}

with previous_rates as (

    select
        currency_code,
        rate_date,
        eur_rate,
        lag(eur_rate) over (partition by currency_code order by rate_date) as previous_eur_rate
    from {{ ref('stg_ecb__exchange_rates') }}

),

daily_returns as (

    select
        *,
        eur_rate / previous_eur_rate - 1 as daily_return
    from previous_rates

)

select
    *,
    -- Volatility = standard deviation of the last 20 daily returns (~1 month),
    -- annualised with the usual 252 trading days per year
    stddev_samp(daily_return) over (
        partition by currency_code order by rate_date
        rows between 19 preceding and current row
    ) * sqrt(252) as volatility_20d_annualised
from daily_returns
