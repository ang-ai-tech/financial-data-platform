{#
    Month-over-month and year-over-year changes.
    Self-joins on the calendar month (not lag()) so that a missing month produces a null
    change instead of silently comparing against the wrong period.
#}

with monthly as (

    select series_id, month_start, value
    from {{ ref('int_macro__monthly') }}

)

select
    cur.series_id,
    cur.month_start,
    cur.value,
    cur.value - prev_month.value                            as mom_change,
    cur.value - prev_year.value                             as yoy_change,
    cur.value / nullif(prev_year.value, 0) - 1              as yoy_pct_change
from monthly as cur
left join monthly as prev_month
    on  prev_month.series_id = cur.series_id
    and prev_month.month_start = (cur.month_start - interval '1 month')::date
left join monthly as prev_year
    on  prev_year.series_id = cur.series_id
    and prev_year.month_start = (cur.month_start - interval '12 months')::date
