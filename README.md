# Marketing Insight Pipeline - Capstone Project

## Project Purpose

This capstone project implements a **comprehensive data engineering pipeline** that combines **batch processing** and **real-time streaming** to deliver marketing analytics insights. The system processes historical sales data alongside real-time market indicators (Bitcoin prices and news events) to create a unified analytical platform.

### Key Features:
- **Batch Processing**: Historical sales, customer, and marketing data using dbt transformations
- **Real-time Streaming**: Live Bitcoin prices and news events via Kafka
- **Data Warehouse**: Snowflake-based architecture with proper schema organization
- **Orchestration**: dbt Cloud scheduling and GitHub Actions CI/CD
- **Data Quality**: Comprehensive testing with 51+ data quality tests
- **Modeling**: Dimensional modeling approach with star schema design

---

## Project Architecture

### High-Level Data Flow

```mermaid
graph TB
    subgraph "Data Sources"
        API1[CoinGecko API<br/>Bitcoin Prices]
        API2[NewsAPI<br/>Market News]
        CSV[CSV Files<br/>Historical Data]
    end

    subgraph "Kafka Streaming Layer"
        K[Kafka Cluster<br/>Docker]
        PROD[Producer<br/>Real Data]
        CONS[Consumer<br/>Snowflake]
    end

    subgraph "Snowflake Data Warehouse"
        subgraph "STREAMING Schema"
            BTC_RAW[bitcoin_prices_raw]
            NEWS_RAW[news_events_raw]
        end

        subgraph "RAW Schema"
            CUST[customers]
            SALES[online_sales]
            MARKET[marketing_spend]
            DISC[discount_coupon]
            TAX[tax_amount]
        end

        subgraph "DBT_SKAMRA_STREAMING Schema"
            STG_BTC[stg_bitcoin]
            STG_NEWS[stg_news]
        end

        subgraph "DBT_SKAMRA_ANALYTICS Schema"
            subgraph "Staging Views"
                STG_C[stg_customers]
                STG_S[stg_online_sales]
                STG_M[stg_marketing_spend]
                STG_D[stg_discount_coupon]
                STG_T[stg_tax_amount]
            end

            subgraph "Dimension Tables"
                DIM_C[dim_customer]
                DIM_P[dim_products]
                DIM_D[dim_datetime]
            end

            subgraph "Fact Tables"
                FCT_S[fct_sales]
            end
        end
    end

    subgraph "Orchestration"
        DBT_CLOUD[dbt Cloud<br/>Scheduled Jobs]
        GITHUB[GitHub Actions<br/>CI/CD]
    end

    API1 --> PROD
    API2 --> PROD
    PROD --> K
    K --> CONS
    CONS --> BTC_RAW
    CONS --> NEWS_RAW

    CSV --> CUST
    CSV --> SALES
    CSV --> MARKET
    CSV --> DISC
    CSV --> TAX

    BTC_RAW --> STG_BTC
    NEWS_RAW --> STG_NEWS

    CUST --> STG_C
    SALES --> STG_S
    MARKET --> STG_M
    DISC --> STG_D
    TAX --> STG_T

    STG_C --> DIM_C
    STG_S --> DIM_P
    STG_S --> DIM_D
    STG_C --> DIM_D

    STG_S --> FCT_S
    STG_M --> FCT_S
    STG_D --> FCT_S
    STG_T --> FCT_S
    DIM_C --> FCT_S
    DIM_P --> FCT_S
    DIM_D --> FCT_S

    DBT_CLOUD --> STG_BTC
    DBT_CLOUD --> STG_NEWS
    DBT_CLOUD --> FCT_S

    GITHUB --> DBT_CLOUD
```

### Data Processing Layers

1. **Raw Layer**:
   - `STREAMING` schema: Real-time data from Kafka (bitcoin_prices_raw, news_events_raw)
   - `RAW` schema: Historical CSV data (customers, online_sales, marketing_spend, etc.)

2. **Staging Layer**:
   - `DBT_SKAMRA_STREAMING`: Processed streaming data (stg_bitcoin, stg_news)
   - `DBT_SKAMRA_ANALYTICS`: Processed batch data (5 staging views)

3. **Analytics Layer**:
   - `DBT_SKAMRA_ANALYTICS`: Business-ready tables (3 dimensions + 1 fact table)

---

## Entity Relationship Diagram (ERD)

### Data Model: Star Schema Design

```mermaid
erDiagram
    dim_customer {
        string customer_id PK
        string gender
        string location
        string segment
        string education
        string marital_status
        string profession
        date customer_since
    }

    dim_products {
        string product_sku PK
        string category
        string gst_rate
        string product_group
        string product_name
    }

    dim_datetime {
        date date_day PK
        int year
        int month
        int day
        string month_name
        boolean is_weekend
        boolean is_holiday
        int quarter
    }

    fct_sales {
        string transaction_id PK
        string customer_id FK
        string product_sku FK
        date transaction_date FK
        int quantity
        decimal unit_price
        decimal gross_amount
        decimal coupon_discount
        decimal tax_amount
        decimal net_amount
        decimal total_amount
    }

    stg_bitcoin {
        string id PK
        string source
        decimal price
        decimal change_24h
        string volatility_category
        timestamp event_timestamp
        date event_date
        int event_hour
        boolean price_valid
    }

    stg_news {
        string id PK
        string source
        string headline
        string description
        string category
        string source_name
        string url
        timestamp published_at
        int word_count
        boolean has_crypto_mention
        timestamp event_timestamp
        string content_category
        string source_category
        int headline_length_category
    }

    dim_customer ||--o{ fct_sales : "customer_id"
    dim_products ||--o{ fct_sales : "product_sku"
    dim_datetime ||--o{ fct_sales : "transaction_date"
```

### ERD Rationale

**Star Schema Design Choice:**
- **Business User Friendly**: Intuitive fact/dimension structure for analysts
- **Performance Optimized**: Denormalized design minimizes JOINs for analytical queries
- **Scalable**: Easy to add new dimensions without affecting existing structure
- **Time Intelligence**: Complete date dimension supports time-series analysis

**Streaming Data Integration:**
- Separate staging models for real-time data (Bitcoin, News) to avoid mixing with batch processing
- Event timestamp preservation for temporal analysis
- Data quality flags and categorization for analytical insights

---

## Grading Criteria Implementation

### ✅ CI/CD Setup (5 points)
**Implementation:**
- GitHub Actions workflow: `.github/workflows/dbt_ci.yml`
- Automated dbt tests and linting on pull requests
- Integration with dbt Cloud for production deployments

**Test Commands:**
```bash
# Run CI workflow locally (requires GitHub CLI)
gh workflow run dbt_ci.yml

# Check workflow status
gh run list --workflow=dbt_ci.yml
```

### ✅ Streaming Data Ingestion (15 points total)

#### Kafka Pipeline (10 points)
**Implementation:**
- Kafka cluster via Docker Compose: `kafka_streaming/docker-compose.yml`
- Producer: `kafka_streaming/producer_real_data.py` (CoinGecko + NewsAPI)
- Consumer: `kafka_streaming/consumer_snowflake.py` (Snowflake integration)
- Topics: `bitcoin-prices`, `news-events`

**Test Commands:**
```bash
# Start Kafka cluster
cd kafka_streaming
docker-compose up -d

# Run producer (in separate terminal)
python producer_real_data.py

# Run consumer (in separate terminal)
python consumer_snowflake.py

# Verify data ingestion
# Check Snowflake STREAMING schema tables
```

#### Real-time Data Landing (5 points)
**Implementation:**
- Data latency: ~30 seconds for Bitcoin, ~60 seconds for News
- Direct Snowflake ingestion via consumer
- Tables: `STREAMING.bitcoin_prices_raw`, `STREAMING.news_events_raw`

### ✅ dbt Project Setup & Development (25 points total)

#### Orchestration Tool (5 points)
**Implementation:**
- dbt Cloud with scheduled jobs
- Job: "Streaming Data Materialization" (hourly)
- Command: `dbt run --select tag:streaming`

**Test Commands:**
```bash
# Test dbt Cloud connection
dbt debug

# Manual job trigger
# Via dbt Cloud UI or API
```

#### Model Creation (5 points)
**Implementation:**
- 11 total dbt models across staging and marts layers
- Medallion architecture: Bronze → Silver → Gold
- Models: 5 staging views + 3 dimension tables + 1 fact table + 2 streaming models

**Test Commands:**
```bash
cd dbt_pipeline

# Run all models
dbt run

# Run specific layers
dbt run --select marts
dbt run --select stg
dbt run --select tag:streaming
```

#### Incremental Materialization (5 points)
**Implementation:**
- `fct_sales`: Incremental fact table with merge strategy
- `stg_bitcoin`: Incremental streaming model with event_timestamp
- `stg_news`: Incremental streaming model with event_timestamp

**Test Commands:**
```bash
# Test incremental runs
dbt run --select fct_sales
dbt run --select tag:streaming

# Full refresh if needed
dbt run --select fct_sales --full-refresh
```

#### Testing Implementation (5 points)
**Implementation:**
- Generic tests: Primary keys, foreign keys, not_null, unique
- Singular tests: Business logic validation
- Total: 51 tests across all models

**Test Commands:**
```bash
# Run all tests
dbt test

# Run tests by category
dbt test --select stg
dbt test --select marts
dbt test --select tag:streaming

# Specific test types
dbt test --select test_type:generic
dbt test --select test_type:singular
```

#### Custom Macro (5 points)
**Implementation:**
- Custom macro: `calculate_total_amount.sql`
- Jinja logic for dynamic SQL generation
- Used in `fct_sales` model

**Test Commands:**
```bash
# Compile and check macro usage
dbt compile --select fct_sales

# Run model using custom macro
dbt run --select fct_sales
```

### ✅ Documentation (5 points)
**Implementation:**
- Column documentation in schema.yml files
- Model descriptions and business logic
- Data lineage via dbt docs

**Test Commands:**
```bash
# Generate documentation
dbt docs generate

# Serve documentation locally
dbt docs serve
```

### ✅ Data Modeling (10 points)

#### ERD Documentation (5 points)
**Implementation:**
- Comprehensive ERD above
- Star schema design rationale
- Detailed in `dbt_pipeline/DATA_MODELING_APPROACH.md`

#### Modeling Approach (5 points)
**Implementation:**
- **Approach**: Dimensional Modeling with Star Schema
- **Rationale**: Optimized for analytical workloads, business user accessibility
- **Alternative**: Considered Data Vault 2.0 and 3NF, rejected for complexity/performance reasons

### 🔄 ML Model Deployment & Prediction Pipeline (15 points)
**Status**: Pending Implementation
- Basic ML model with data processing, feature selection, training, evaluation
- Model execution orchestration
- Code-based implementation required

### ✅ Bonus & Creativity (15 points available)

#### Additional Tools (10 points)
**Current Tools Used:**
- **Snowflake**: Data warehouse platform
- **Kafka**: Real-time streaming
- **dbt Cloud**: Orchestration and scheduling
- **GitHub Actions**: CI/CD automation
- **Docker**: Containerization

#### Advanced Features (5 points per feature, 5 max)
**Current Features:**
- **Real-time API Integration**: Live data from CoinGecko and NewsAPI
- **Advanced dbt Techniques**: Custom macros, incremental models, comprehensive testing
- **Production Orchestration**: Automated scheduling with dbt Cloud

---

## Testing & Validation Commands

### Complete Pipeline Test
```bash
# 1. Test dbt project
cd dbt_pipeline
dbt debug
dbt deps
dbt run
dbt test

# 2. Test streaming pipeline
cd ../kafka_streaming
docker-compose up -d
python producer_real_data.py &
python consumer_snowflake.py &

# 3. Test incremental processing
cd ../dbt_pipeline
dbt run --select tag:streaming

# 4. Validate data quality
dbt test --select tag:streaming
```

### Individual Component Tests
```bash
# Test batch processing
dbt run --select marts
dbt test --select marts

# Test streaming processing
dbt run --select stream_stg
dbt test --select stream_stg

# Test specific models
dbt run --select fct_sales
dbt test --select fct_sales

# Test data relationships
dbt test --select test_type:relationship
```

### Performance & Monitoring
```bash
# Check model performance
dbt run --select fct_sales --profiles-dir .

# Generate fresh documentation
dbt docs generate
dbt docs serve

# Check logs
tail -f logs/dbt.log
```

### Demo Commands for Live Presentation
```bash
# Complete pipeline demonstration
cd dbt_pipeline

echo "=== Testing dbt Connection ==="
dbt debug

echo "=== Installing Dependencies ==="
dbt deps

echo "=== Running All Models ==="
dbt run

echo "=== Running All Tests (51 total) ==="
dbt test

echo "=== Showing Model Lineage ==="
dbt docs generate
dbt docs serve

echo "=== Testing Streaming Models ==="
dbt run --select tag:streaming
dbt test --select tag:streaming

echo "=== Testing Incremental Loads ==="
dbt run --select fct_sales

echo "=== Testing Custom Macro ==="
dbt compile --select fct_sales

echo "=== Testing by Layer ==="
dbt test --select marts
dbt test --select stg
```

---

## Current Score: 47/90 Points

**Completed:**
- ✅ Streaming Data Ingestion: 15/15 points
- ✅ dbt Project Setup & Development: 25/25 points
- ✅ Documentation: 5/5 points
- ✅ Data Modeling: 10/10 points
- ✅ Bonus Features: ~7/15 points

**Pending:**
- 🔄 CI/CD Setup: 0/5 points (needs demonstration)
- 🔄 ML Model Pipeline: 0/15 points (needs implementation)

**Next Steps:**
1. Demonstrate CI/CD workflow functionality
2. Implement and deploy ML model pipeline
3. Potentially add more bonus features (monitoring, visualization, advanced analytics)

---

## Quick Start Guide

1. **Clone Repository**: `git clone <repository-url>`
2. **Setup dbt**: `cd dbt_pipeline && dbt deps`
3. **Configure Snowflake**: Update connection details in `profiles.yml`
4. **Start Streaming**: `cd kafka_streaming && docker-compose up -d`
5. **Run Pipeline**: `dbt run && dbt test`
6. **Monitor**: Check dbt Cloud dashboard for scheduled jobs

This comprehensive pipeline demonstrates modern data engineering practices with both batch and real-time processing capabilities.
