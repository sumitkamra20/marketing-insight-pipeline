{{
    config(
        materialized='table'
    )
}}

with product_base as (
    select distinct
        product_sku,
        product_description,
        product_category
    from {{ ref('stg_online_sales') }}
),

tax_info as (
    select
        product_category,
        gst as gst_rate
    from {{ ref('stg_tax_amount') }}
),

products_enhanced as (
    select
        p.product_sku,
        p.product_description,
        p.product_category,
        coalesce(t.gst_rate, 0) as gst_rate,
                -- Add product category grouping for analysis
        case
            when p.product_category in ('Nest-USA', 'Nest-Canada', 'Nest', 'Google', 'Android', 'Waze') then 'Technology'
            when p.product_category in ('Apparel', 'Accessories', 'Headgear') then 'Fashion & Apparel'
            when p.product_category in ('Bags', 'Backpacks', 'More Bags') then 'Bags & Storage'
            when p.product_category in ('Drinkware', 'Bottles', 'Housewares', 'Lifestyle') then 'Lifestyle & Home'
            when p.product_category in ('Office', 'Notebooks & Journals') then 'Office & Stationery'
            when p.product_category in ('Fun', 'Gift Cards') then 'Gifts & Entertainment'
            else 'Other'
        end as product_group
    from product_base p
    left join tax_info t
        on p.product_category = t.product_category
)

select * from products_enhanced
