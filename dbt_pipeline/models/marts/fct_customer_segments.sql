{{
  config(
    materialized='table',
    description='Customer segmentation facts with RFM analysis and business metrics'
  )
}}

with customer_segments as (
    select * from {{ ref('customer_segments') }}
),

customer_dim as (
    select * from {{ ref('dim_customer') }}
),

customer_sales_metrics as (
    select
        customer_id,
        count(distinct transaction_id) as total_orders,
        sum(quantity) as total_quantity,
        sum(total_amount) as total_revenue,
        min(transaction_date) as first_purchase_date,
        max(transaction_date) as last_purchase_date,
        datediff('day', max(transaction_date), current_date()) as days_since_last_purchase,
        datediff('day', min(transaction_date), max(transaction_date)) as customer_lifetime_days,
        avg(total_amount) as avg_order_value
    from {{ ref('fct_sales') }}
    where customer_id is not null
    group by customer_id
),

final as (
        select
        -- Customer identifiers
        cs.customer_id,
        cd.location,
        cd.gender,
        cd.customer_tenure_months,

        -- Segmentation
        cs.segment_id,
        cs.segment_name,

        -- RFM and business metrics
        sm.total_orders,
        sm.total_quantity,
        sm.total_revenue,
        sm.first_purchase_date,
        sm.last_purchase_date,
        sm.days_since_last_purchase,
        sm.customer_lifetime_days,
        sm.avg_order_value,

        -- Calculated metrics
        case
            when sm.customer_lifetime_days > 0
            then sm.total_revenue / sm.customer_lifetime_days
            else sm.total_revenue
        end as daily_revenue_rate,

        case
            when sm.days_since_last_purchase <= 30 then 'Active'
            when sm.days_since_last_purchase <= 90 then 'Recent'
            when sm.days_since_last_purchase <= 180 then 'Dormant'
            else 'Inactive'
        end as activity_status,

        -- Metadata
        current_timestamp() as updated_at

    from customer_segments cs
    left join customer_dim cd on cs.customer_id = cd.customer_id
    left join customer_sales_metrics sm on cs.customer_id = sm.customer_id
)

select * from final
