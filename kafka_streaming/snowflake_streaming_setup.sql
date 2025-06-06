USE ROLE ACCOUNTADMIN;

--------------------------------------------------------------------------------
-- Create streaming user for Kafka ingestion (separate from dbt user)
--------------------------------------------------------------------------------
CREATE USER IF NOT EXISTS kafka_streaming
  PASSWORD       = 'kafkaPassword123'
  LOGIN_NAME     = 'kafka_streaming'
  MUST_CHANGE_PASSWORD = FALSE
  DEFAULT_WAREHOUSE    = 'MARKETING_WH'
  DEFAULT_ROLE         = TRANSFORM
  DEFAULT_NAMESPACE    = 'MARKETING_INSIGHTS_DB.STREAMING'
  COMMENT = 'Kafka streaming user for real-time data ingestion';

-- Set as service user
ALTER USER kafka_streaming SET TYPE = LEGACY_SERVICE;

-- Grant the TRANSFORM role to the streaming user
GRANT ROLE TRANSFORM TO USER kafka_streaming;

--------------------------------------------------------------------------------
-- Create STREAMING schema for real-time data
--------------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS MARKETING_INSIGHTS_DB.STREAMING;

--------------------------------------------------------------------------------
-- Grant TRANSFORM role privileges on the STREAMING schema
--------------------------------------------------------------------------------
-- Full control on the STREAMING schema
GRANT ALL ON SCHEMA MARKETING_INSIGHTS_DB.STREAMING TO ROLE TRANSFORM;
GRANT ALL ON ALL TABLES IN SCHEMA MARKETING_INSIGHTS_DB.STREAMING TO ROLE TRANSFORM;
GRANT ALL ON FUTURE TABLES IN SCHEMA MARKETING_INSIGHTS_DB.STREAMING TO ROLE TRANSFORM;

-- Verify permissions
SHOW GRANTS TO ROLE TRANSFORM;
SHOW GRANTS TO USER kafka_streaming;

-- Test connection (optional)
-- USE ROLE TRANSFORM;
-- USE WAREHOUSE MARKETING_WH;
-- USE DATABASE MARKETING_INSIGHTS_DB;
-- USE SCHEMA STREAMING;
-- SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
