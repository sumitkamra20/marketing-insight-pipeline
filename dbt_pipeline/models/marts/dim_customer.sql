{{
    config(
        materialized='table'
    )
}}

with customer_base as (
    select
        customerid as customer_id,
        gender,
        location,
        customer_tenure_months
    from {{ ref('stg_customers') }}
),

customer_enhanced as (
    select
        customer_id,
        gender,
        location,
        customer_tenure_months,
        -- Add customer segments based on tenure
        case
            when customer_tenure_months < 6 then 'New Customer'
            when customer_tenure_months between 6 and 12 then 'Developing Customer'
            when customer_tenure_months between 13 and 24 then 'Established Customer'
            else 'Loyal Customer'
        end as customer_segment,
        -- Add tenure years for easier analysis
        round(customer_tenure_months / 12.0, 1) as customer_tenure_years
    from customer_base
)

select * from customer_enhanced
