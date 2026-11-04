with days as (

    select generate_series(
        '{{ var("calendar_start_date") }}'::date,
        (current_date + interval '1 year')::date,
        interval '1 day'
    )::date as date_day

)

select
    date_day,
    extract(year from date_day)::int        as year,
    extract(quarter from date_day)::int     as quarter,
    extract(month from date_day)::int       as month,
    to_char(date_day, 'Mon')                as month_name,
    date_trunc('month', date_day)::date     as month_start,
    extract(week from date_day)::int        as iso_week,
    extract(isodow from date_day)::int      as day_of_week,  -- 1 = Monday
    extract(isodow from date_day) in (6, 7) as is_weekend
from days
