{% snapshot customer_history %}

    {{
        config(
          target_database='MARKETING_INSIGHTS_DB',
          target_schema='snapshots',
          unique_key='customer_id',
          strategy='check',
          check_cols='all',
        )
    }}

    select
        customer_id,
        gender,
        location,
        customer_tenure_months,
        customer_segment,
        customer_tenure_years
    from {{ ref('dim_customer') }}

{% endsnapshot %}
