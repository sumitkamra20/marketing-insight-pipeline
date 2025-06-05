-- Test: Total amount should always be greater than or equal to net sales amount
-- This ensures our financial calculations are logical

select
    transaction_id,
    net_sales_amount,
    total_amount,
    (total_amount - net_sales_amount) as difference
from {{ ref('fct_sales') }}
where total_amount < net_sales_amount
