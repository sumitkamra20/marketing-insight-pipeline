{{
    config(
        materialized='view'
    )
}}

select
    customerid,
    gender,
    location,
    tenure_months as customer_tenure_months
from {{ source('raw', 'customers') }}
