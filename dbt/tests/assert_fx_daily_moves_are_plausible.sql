-- A daily move above 15% for a major currency against the euro almost certainly means
-- bad data (wrong unit, misplaced decimal) rather than a real market event.
select currency_code, rate_date, previous_eur_rate, eur_rate, daily_return
from {{ ref('fct_fx_rates_daily') }}
where abs(daily_return) > 0.15
