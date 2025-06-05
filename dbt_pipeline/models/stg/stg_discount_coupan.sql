{{
    config(
        materialized='view'
    )
}}

select
    month as coupon_month,
    product_category,
    coupon_code,
    discount_pct
from {{ source('raw', 'discount_coupon') }}
