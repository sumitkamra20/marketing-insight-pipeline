# Data Modeling Approach: Dimensional Modeling (Star Schema)

## Overview
This project implements a **Dimensional Modeling** approach using the **Star Schema** pattern, optimized for analytical workloads and business intelligence.

## Architecture: Medallion with Star Schema

### Bronze Layer (Sources)
- **Raw Snowflake Tables**: Direct CSV ingestion
- **Tables**: customers, online_sales, marketing_spend, discount_coupon, tax_amount
- **Purpose**: Unprocessed source data with minimal transformations

### Silver Layer (Staging - `stg/`)
- **Models**: stg_customers, stg_online_sales, stg_marketing_spend, stg_discount_coupan, stg_tax_amount
- **Purpose**: Data cleaning, type casting, basic transformations
- **Materialization**: Views (for lightweight processing)

### Gold Layer (Marts - `marts/`)
- **Fact Table**: fct_sales (line-item grain)
- **Dimension Tables**: dim_customer, dim_products, dim_datetime
- **Purpose**: Business-ready analytics tables
- **Materialization**: Tables (for performance)

## Star Schema Design

```
       ┌─────────────┐      ┌─────────────┐
       │dim_customer │      │dim_products │
       │             │      │             │
       │customer_id  │      │product_sku  │
       │gender       │      │category     │
       │location     │      │gst_rate     │
       │segment      │      │product_group│
       └──────┬──────┘      └──────┬──────┘
              │                    │
              │   ┌─────────────┐  │
              └───┤  fct_sales  ├──┘
                  │             │
                  │transaction  │
                  │customer_id  │
                  │product_sku  │
                  │quantity     │
                  │amounts...   │
                  └──────┬──────┘
                         │
              ┌─────────────┐
              │dim_datetime │
              │             │
              │date_day     │
              │year/month   │
              │weekday flags│
              └─────────────┘
```

## Why Dimensional Modeling?

### 1. **Business User Friendly**
- Intuitive fact/dimension structure
- Clear business concepts (customers, products, sales)
- Easy to understand and query

### 2. **Performance Optimized**
- Denormalized for fast aggregations
- Star schema minimizes JOINs
- Pre-calculated metrics in fact table

### 3. **Analytical Workload Ready**
- Supports OLAP operations
- Time-series analysis via dim_datetime
- Flexible slice-and-dice capabilities

### 4. **Scalable Design**
- Easy to add new dimensions
- Fact table can grow independently
- Supports both detailed and summary queries

## Business Logic Implementation

### Fact Table Grain
- **Line Item Level**: Each row = one product in one transaction
- **Additive Facts**: All monetary amounts can be summed
- **Calculated Metrics**: Gross, net, tax, total amounts

### Dimension Design
- **Type 1 SCD**: Current state dimensions (no history tracking)
- **Business Hierarchies**: Customer segments, product groups
- **Time Intelligence**: Complete date dimension for time-series analysis

## Alternative Approaches Considered

### Data Vault 2.0
- **Pros**: Better for data lineage, change tracking
- **Cons**: Complex for analysts, more JOINs required
- **Decision**: Overkill for this analytical use case

### One Big Table (OBT)
- **Pros**: Simple queries, no JOINs
- **Cons**: Data redundancy, update complexity
- **Decision**: Star schema provides better balance

### 3NF (Third Normal Form)
- **Pros**: No data redundancy, referential integrity
- **Cons**: Many JOINs required, poor analytical performance
- **Decision**: Star schema better for analytics

## Implementation Details

### Materialization Strategy
- **Staging**: Views (lightweight, always fresh)
- **Dimensions**: Tables (stable reference data)
- **Facts**: Tables + Incremental (performance + efficiency)

### Data Quality
- Generic tests for primary keys and relationships
- Singular tests for business logic validation
- Comprehensive documentation for all models

This approach optimizes for analytical performance while maintaining data quality and business user accessibility.
