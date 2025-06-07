-- Customer Segmentation Analysis
-- This analysis shows the distribution of customers across ML-generated segments
-- and key business metrics for each segment

select
    segment_name,
    segment_id,
    count(*) as customer_count,

    -- Revenue metrics
    sum(total_revenue) as total_segment_revenue,
    avg(total_revenue) as avg_customer_revenue,

    -- Order metrics
    sum(total_orders) as total_segment_orders,
    avg(total_orders) as avg_orders_per_customer,
    avg(avg_order_value) as avg_order_value_per_customer,

    -- Activity metrics
    sum(case when activity_status = 'Active' then 1 else 0 end) as active_customers,
    sum(case when activity_status = 'Recent' then 1 else 0 end) as recent_customers,
    sum(case when activity_status = 'Dormant' then 1 else 0 end) as dormant_customers,
    sum(case when activity_status = 'Inactive' then 1 else 0 end) as inactive_customers,

    -- Customer characteristics
    round(avg(customer_tenure_months), 1) as avg_tenure_months,

    -- Performance ratios
    round(100.0 * count(*) / sum(count(*)) over(), 2) as customer_percentage,
    round(100.0 * sum(total_revenue) / sum(sum(total_revenue)) over(), 2) as revenue_percentage

from {{ ref('fct_customer_segments') }}
group by segment_name, segment_id
order by total_segment_revenue desc
