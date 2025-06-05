{{
    config(
        materialized='view'
    )
}}

select
    product_category,
    gst
from {{ source('raw', 'tax_amount') }}
