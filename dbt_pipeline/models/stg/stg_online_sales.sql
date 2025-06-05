{{
    config(
        materialized='view'
    )
}}

{{ config(materialized='view') }}

with raw_sales as (
  select
    customerid          as customer_id,      -- NUMBER
    transaction_id      as transaction_id,   -- NUMBER
    transaction_date    as raw_txn_date,     -- TEXT (e.g. “1/1/2019”)
    product_sku         as product_sku,      -- TEXT (14 chars)
    product_description as product_desc,     -- TEXT (~59 chars)
    product_category    as product_category, -- TEXT (up to 20 chars)
    quantity            as quantity,         -- NUMBER
    avg_price           as avg_price,        -- FLOAT
    delivery_charges    as delivery_charges, -- FLOAT
    coupon_status       as coupon_status     -- TEXT (e.g. “Used” / “Not_Used”)
  from {{ source('raw','online_sales') }}
)

select
  customer_id,
  transaction_id,
  try_to_date(raw_txn_date, 'MM/DD/YYYY') as transaction_date,
  product_sku,
  product_desc        as product_description,
  product_category,
  quantity::NUMBER(38,0)       as quantity,
  avg_price::FLOAT             as avg_price,
  delivery_charges::FLOAT      as delivery_charges,
  coupon_status                as coupon_status
from raw_sales
