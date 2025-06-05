-- Test: Discount amount should be reasonable (not more than 50% of gross sales)
-- This catches any unrealistic discount calculations

select
    transaction_id,
    product_sku,
    gross_sales_amount,
    discount_amount,
    (discount_amount / gross_sales_amount * 100) as discount_percentage_actual
from {{ ref('fct_sales') }}
where discount_amount > (gross_sales_amount * 0.5)  -- More than 50% discount seems unrealistic
   or discount_amount < 0  -- Negative discounts don't make business sense
