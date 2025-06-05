{{
    config(
        materialized='table'
    )
}}

with date_spine as (
    -- Generate a date range covering your data period
    -- Adjust start and end dates based on your actual data range
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2019-01-01' as date)",
        end_date="cast('2020-12-31' as date)"
    ) }}
),

datetime_enhanced as (
    select
        date_day,

        -- Basic date components
        extract(year from date_day) as year,
        extract(month from date_day) as month,
        extract(day from date_day) as day,
        extract(quarter from date_day) as quarter,
        extract(week from date_day) as week_of_year,
        extract(dayofweek from date_day) as day_of_week,
        extract(dayofyear from date_day) as day_of_year,

        -- Formatted date strings
        to_char(date_day, 'YYYY-MM') as year_month,
        to_char(date_day, 'YYYY-Q') as year_quarter,
        to_char(date_day, 'Month') as month_name_full,
        to_char(date_day, 'Day') as day_name_full,

                -- Business logic flags
        case
            when extract(dayofweek from date_day) in (0, 6) then false
            else true
        end as is_weekday,

        case
            when extract(dayofweek from date_day) in (0, 6) then true
            else false
        end as is_weekend,

        -- Month start/end flags
        case
            when extract(day from date_day) = 1 then true
            else false
        end as is_month_start,

        case
            when date_day = last_day(date_day) then true
            else false
        end as is_month_end,

        -- Quarter start/end flags
        case
            when extract(month from date_day) in (1, 4, 7, 10) and extract(day from date_day) = 1 then true
            else false
        end as is_quarter_start,

        case
            when extract(month from date_day) in (3, 6, 9, 12) and date_day = last_day(date_day) then true
            else false
        end as is_quarter_end,

        -- Year start/end flags
        case
            when extract(month from date_day) = 1 and extract(day from date_day) = 1 then true
            else false
        end as is_year_start,

        case
            when extract(month from date_day) = 12 and extract(day from date_day) = 31 then true
            else false
        end as is_year_end,

     from date_spine
)

select * from datetime_enhanced
