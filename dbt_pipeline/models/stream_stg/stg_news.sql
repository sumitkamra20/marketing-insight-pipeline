{{ config(
    materialized='incremental',
    unique_key='id',
    on_schema_change='fail',
    tags=['streaming', 'realtime'],
    schema='streaming'
) }}

WITH news_cleaned AS (
    SELECT
        id,
        source,
        headline,
        description,
        category,
        source_name,
        url,
        published_at,
        word_count,
        has_crypto_mention,
        event_timestamp,
        ingestion_timestamp,

        -- Add analytical columns
        CASE
            WHEN word_count >= 10 THEN 'DETAILED'
            WHEN word_count >= 5 THEN 'MODERATE'
            ELSE 'BRIEF'
        END AS headline_length_category,

        -- Time-based columns for analysis
        DATE(event_timestamp) AS news_date,
        HOUR(event_timestamp) AS news_hour,
        DAYOFWEEK(event_timestamp) AS day_of_week,

        -- Published vs processed timing
        DATEDIFF('MINUTE', published_at, event_timestamp) AS processing_delay_minutes,

        -- Content analysis flags
        CASE
            WHEN UPPER(headline) LIKE '%BITCOIN%' THEN TRUE
            WHEN UPPER(headline) LIKE '%CRYPTO%' THEN TRUE
            WHEN UPPER(description) LIKE '%BITCOIN%' THEN TRUE
            WHEN UPPER(description) LIKE '%CRYPTO%' THEN TRUE
            ELSE FALSE
        END AS explicit_crypto_mention,

        -- Source categorization
        CASE
            WHEN UPPER(source_name) LIKE '%BBC%' THEN 'BROADCAST'
            WHEN UPPER(source_name) LIKE '%CNN%' THEN 'BROADCAST'
            WHEN UPPER(source_name) LIKE '%REUTERS%' THEN 'WIRE_SERVICE'
            ELSE 'OTHER'
        END AS source_category,

        -- Data quality flags
        CASE
            WHEN headline IS NULL OR TRIM(headline) = '' THEN FALSE
            WHEN source_name IS NULL OR TRIM(source_name) = '' THEN FALSE
            WHEN published_at IS NULL THEN FALSE
            ELSE TRUE
        END AS is_valid_record,

        -- Processing metadata
        CURRENT_TIMESTAMP() AS dbt_updated_at

    FROM {{ source('streaming', 'news_events_raw') }}

    {% if is_incremental() %}
        WHERE event_timestamp > (SELECT MAX(event_timestamp) FROM {{ this }})
    {% endif %}
)

SELECT * FROM news_cleaned
WHERE is_valid_record = TRUE
