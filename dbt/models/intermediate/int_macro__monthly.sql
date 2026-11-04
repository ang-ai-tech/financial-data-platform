{#
    Bring every series to a monthly grain.
    Monthly series pass through unchanged; daily series (e.g. DGS10) become a monthly average.
#}

select
    series_id,
    date_trunc('month', observation_date)::date as month_start,
    avg(value)                                  as value,
    count(*)                                    as observation_count
from {{ ref('stg_fred__observations') }}
group by 1, 2
