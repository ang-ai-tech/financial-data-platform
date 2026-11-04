{#
    One row per month for the dashboard: EUR/USD next to the main US indicators.
#}

with eur_usd as (

    select
        month_start,
        avg_eur_rate        as eur_usd_avg,
        month_end_eur_rate  as eur_usd_month_end,
        month_end_eur_rate / lag(month_end_eur_rate) over (order by month_start) - 1
                            as eur_usd_mom_pct_change
    from {{ ref('int_fx_rates__monthly') }}
    where currency_code = 'USD'

),

macro as (

    select
        month_start,
        max(yoy_pct_change) filter (where series_id = 'CPIAUCSL')  as us_cpi_yoy_pct,
        max(value)          filter (where series_id = 'UNRATE')    as us_unemployment_rate,
        max(value)          filter (where series_id = 'FEDFUNDS')  as us_fed_funds_rate,
        max(value)          filter (where series_id = 'DGS10')     as us_10y_treasury_yield
    from {{ ref('fct_macro_indicators_monthly') }}
    group by month_start

)

select
    eur_usd.month_start,
    eur_usd.eur_usd_avg,
    eur_usd.eur_usd_month_end,
    eur_usd.eur_usd_mom_pct_change,
    macro.us_cpi_yoy_pct,
    macro.us_unemployment_rate,
    macro.us_fed_funds_rate,
    macro.us_10y_treasury_yield
from eur_usd
left join macro using (month_start)
