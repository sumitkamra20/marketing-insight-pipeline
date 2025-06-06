{{ config(
    materialized='incremental',
    unique_key='id',
    on_schema_change='fail',
    tags=['streaming', 'realtime'],
    schema='streaming'
) }}

WITH bitcoin_cleaned AS (
    SELECT
        id,
        source,
        price,
        change_24h,
        event_timestamp,
        ingestion_timestamp,

        -- Add basic analytical columns
        CASE
            WHEN ABS(change_24h) >= 5.0 THEN 'HIGH_VOLATILITY'
            WHEN ABS(change_24h) >= 2.0 THEN 'MEDIUM_VOLATILITY'
            ELSE 'LOW_VOLATILITY'
        END AS volatility_category,

        -- Time-based columns for analysis
        DATE(event_timestamp) AS price_date,
        HOUR(event_timestamp) AS price_hour,
        DAYOFWEEK(event_timestamp) AS day_of_week,

        -- Lag analysis preparation (for downstream models)
        LAG(price) OVER (ORDER BY event_timestamp) AS previous_price,

        -- Data quality flags
        CASE
            WHEN price IS NULL THEN FALSE
            WHEN price <= 0 THEN FALSE
            WHEN change_24h IS NULL THEN FALSE
            ELSE TRUE
        END AS is_valid_record,

        -- Processing metadata
        CURRENT_TIMESTAMP() AS dbt_updated_at

    FROM {{ source('streaming', 'bitcoin_prices_raw') }}

    {% if is_incremental() %}
        WHERE event_timestamp > (SELECT MAX(event_timestamp) FROM {{ this }})
    {% endif %}
)

SELECT * FROM bitcoin_cleaned
WHERE is_valid_record = TRUE
