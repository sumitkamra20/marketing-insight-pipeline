{{
    config(
        materialized='incremental',
        unique_key='transaction_id'
    )
}}

with sales_base as (
    select
        customer_id,
        transaction_id,
        transaction_date,
        product_sku,
        product_description,
        product_category,
        quantity,
        avg_price,
        delivery_charges,
        coupon_status
    from {{ ref('stg_online_sales') }}

    {% if is_incremental() %}
        -- Only process new transactions on incremental runs
        where transaction_date > (select max(transaction_date) from {{ this }})
    {% endif %}
),

coupon_info as (
    select
        product_category,
        avg(discount_pct) as discount_pct  -- Use average discount for category
    from {{ ref('stg_discount_coupan') }}
    group by product_category
),

tax_info as (
    select
        product_category,
        gst as gst_rate
    from {{ ref('stg_tax_amount') }}
),

sales_enhanced as (
    select
        s.transaction_id,
        s.customer_id,
        s.transaction_date,
        s.product_sku,
        s.quantity,
        s.avg_price,
        s.delivery_charges,
        s.coupon_status,

        -- Calculated financial metrics
        (s.quantity * s.avg_price) as gross_sales_amount,

        -- Apply discount if coupon was used
        case
            when s.coupon_status = 'Used' and c.discount_pct is not null
            then (s.quantity * s.avg_price) * (1 - c.discount_pct / 100.0)
            else (s.quantity * s.avg_price)
        end as net_sales_amount,

        -- Add GST amount
        case
            when s.coupon_status = 'Used' and c.discount_pct is not null
            then ((s.quantity * s.avg_price) * (1 - c.discount_pct / 100.0)) * (coalesce(t.gst_rate, 0) / 100.0)
            else (s.quantity * s.avg_price) * (coalesce(t.gst_rate, 0) / 100.0)
        end as gst_amount,

        -- Total amount including GST and delivery
        case
            when s.coupon_status = 'Used' and c.discount_pct is not null
            then ((s.quantity * s.avg_price) * (1 - c.discount_pct / 100.0)) * (1 + coalesce(t.gst_rate, 0) / 100.0) + s.delivery_charges
            else (s.quantity * s.avg_price) * (1 + coalesce(t.gst_rate, 0) / 100.0) + s.delivery_charges
        end as total_amount,

        -- Discount details
        coalesce(c.discount_pct, 0) as discount_percentage,
        case
            when s.coupon_status = 'Used' and c.discount_pct is not null
            then (s.quantity * s.avg_price) * (c.discount_pct / 100.0)
            else 0
        end as discount_amount,

        -- Use custom macro to categorize sales
        {{ categorize_sale_size('(s.quantity * s.avg_price)') }} as sale_size_category,

        -- Use custom macro for audit timestamp
        {{ get_current_timestamp() }} as processed_at

    from sales_base s
    left join coupon_info c
        on s.product_category = c.product_category
        and s.coupon_status = 'Used'
    left join tax_info t
        on s.product_category = t.product_category
)

select * from sales_enhanced
