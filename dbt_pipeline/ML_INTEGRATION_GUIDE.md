# ML Customer Segmentation Integration with dbt

This document describes how we've integrated ML-generated customer segmentation results with the existing dbt pipeline.

## Overview

We've successfully integrated the machine learning customer segmentation model results with our dbt data pipeline using **dbt seeds** and custom mart models. This creates a seamless bridge between ML outputs and business intelligence.

## Integration Architecture

```
ML Pipeline (Python/Jupyter)
    ↓ (exports CSV)
Customer Segments CSV
    ↓ (dbt seed)
Snowflake Table (customer_segments)
    ↓ (dbt model)
Business Mart (fct_customer_segments)
    ↓ (analysis/BI tools)
Business Insights & Actions
```

## Implementation Steps

### 1. ML Model Output
- **Location**: `ml_pipeline/models/customer_segments.csv`
- **Structure**: `customer_id`, `segment_id`, `segment_name`
- **Records**: 1,468 customers segmented into 5 groups

### 2. dbt Seed Configuration
- **File**: `dbt_pipeline/seeds/customer_segments.csv`
- **Configuration**: Added to `dbt_project.yml` with proper data types
- **Schema**: Loaded into `dbt_skamra_analytics.customer_segments`

### 3. Business Mart Model
- **File**: `dbt_pipeline/models/marts/fct_customer_segments.sql`
- **Purpose**: Joins ML segments with customer data and sales metrics
- **Features**:
  - Customer demographics (location, gender, tenure)
  - ML segment classification
  - RFM metrics (total orders, revenue, recency)
  - Activity status categorization
  - Business KPIs (average order value, customer lifetime value)

### 4. Data Quality & Testing
- **Seed Tests**: Validates segment IDs, names, and customer relationships
- **Model Tests**: Ensures data integrity and business rule compliance
- **Results**: All 13 tests passing ✅

## Customer Segments Defined

| Segment ID | Segment Name | Description |
|------------|--------------|-------------|
| 0 | Big Spenders | High-value customers with large transaction amounts |
| 1 | At-Risk (Lapsing) | Previously active customers showing decline |
| 2 | Occasional Shoppers | Regular but moderate purchasing behavior |
| 3 | Champions (VIPs) | Top-tier customers with high value and frequency |
| 4 | Loyal Customers | Consistent, regular customers with good retention |

## Key Features

### Business Metrics Integration
- **Customer Lifetime Value**: Total revenue per customer
- **Purchase Frequency**: Number of orders and average order value
- **Recency Analysis**: Days since last purchase
- **Activity Status**: Active/Recent/Dormant/Inactive classification

### Automated Data Quality
- Referential integrity between segments and customers
- Validation of segment classifications
- Data freshness tracking with `updated_at` timestamps

### Scalable Architecture
- **Incremental Updates**: Easy to refresh with new ML model runs
- **Version Control**: Segments tracked in git with dbt project
- **Lineage Documentation**: Full data lineage from source to insights

## Usage Examples

### 1. Load New Segmentation Results
```bash
# After ML model generates new customer_segments.csv
cp ml_pipeline/models/customer_segments.csv dbt_pipeline/seeds/
dbt seed --select customer_segments
dbt run --select fct_customer_segments
dbt test --select customer_segments fct_customer_segments
```

### 2. Business Analysis
```sql
-- Segment performance analysis
SELECT
    segment_name,
    COUNT(*) as customers,
    AVG(total_revenue) as avg_clv,
    SUM(total_revenue) as segment_revenue
FROM {{ ref('fct_customer_segments') }}
GROUP BY segment_name
ORDER BY segment_revenue DESC;
```

### 3. Marketing Campaign Targeting
```sql
-- Identify high-value at-risk customers for retention campaigns
SELECT customer_id, total_revenue, days_since_last_purchase
FROM {{ ref('fct_customer_segments') }}
WHERE segment_name = 'At-Risk (Lapsing)'
  AND total_revenue > 1000
ORDER BY total_revenue DESC;
```

## Benefits

1. **Unified Data Model**: ML insights integrated with business data
2. **Automated Quality**: Built-in testing and validation
3. **Business Ready**: Segment names and metrics ready for stakeholders
4. **Scalable Process**: Easy to update as model improves
5. **Full Lineage**: Track from raw data through ML to business insights

## Future Enhancements

- **Real-time Scoring**: Integration with streaming pipeline for live segmentation
- **Model Monitoring**: Track segment stability and drift over time
- **Advanced Analytics**: Predictive metrics for segment transition probability
- **Automation**: Scheduled model retraining and segment refresh

## Files Created/Modified

- `dbt_pipeline/seeds/customer_segments.csv` - ML model output
- `dbt_pipeline/seeds/schema.yml` - Seed documentation and testing
- `dbt_pipeline/models/marts/fct_customer_segments.sql` - Business mart
- `dbt_pipeline/models/marts/schema.yml` - Model documentation
- `dbt_pipeline/analyses/customer_segment_analysis.sql` - Example analysis
- `dbt_pipeline/dbt_project.yml` - Seed configuration

## Commands Reference

```bash
# Test the integration
dbt seed --select customer_segments
dbt run --select fct_customer_segments
dbt test --select customer_segments fct_customer_segments

# Full pipeline refresh
dbt build --select customer_segments fct_customer_segments

# Generate documentation
dbt docs generate
dbt docs serve
```

---

This integration demonstrates best practices for combining ML model outputs with enterprise data pipelines, ensuring both technical robustness and business value.
