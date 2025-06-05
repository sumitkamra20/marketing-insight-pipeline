-- Test: Customer segments should be assigned correctly based on tenure
-- This validates our business rules for customer segmentation

select
    customer_id,
    customer_tenure_months,
    customer_segment,
    case
        when customer_tenure_months < 6 then 'New Customer'
        when customer_tenure_months between 6 and 12 then 'Developing Customer'
        when customer_tenure_months between 13 and 24 then 'Established Customer'
        else 'Loyal Customer'
    end as expected_segment
from {{ ref('dim_customer') }}
where customer_segment != case
    when customer_tenure_months < 6 then 'New Customer'
    when customer_tenure_months between 6 and 12 then 'Developing Customer'
    when customer_tenure_months between 13 and 24 then 'Established Customer'
    else 'Loyal Customer'
end
