# Marketing Insight Pipeline - Data Ingestion Guide

## Overview
This document outlines the data conversion and schema analysis performed for the Marketing Insight ELT pipeline, preparing data for Snowflake ingestion.

## Data Files Overview

### Raw Data Location: `data/raw/`
- **Total Files**: 5 (originally 3 CSV + 2 Excel files)
- **After Conversion**: 7 files (5 CSV + 2 original Excel files)

### File Details

#### 1. CustomersData (converted from .xlsx)
- **Rows**: 1,468 customers
- **Columns**: 4
- **Key Fields**: CustomerID (unique), Gender, Location, Tenure_Months
- **Data Quality**: No nulls, all fields populated

#### 2. Tax_amount (converted from .xlsx)
- **Rows**: 20 product categories
- **Columns**: 2
- **Key Fields**: Product_Category, GST (tax rate)
- **Data Quality**: No nulls, GST rates range from 0.1 to 0.18

#### 3. Online_Sales (existing CSV)
- **Rows**: 52,924 transactions
- **Columns**: 10
- **Key Fields**: CustomerID, Transaction_ID, Transaction_Date, Product_SKU, etc.
- **Data Quality**: No nulls, comprehensive transaction data

#### 4. Marketing_Spend (existing CSV)
- **Rows**: 365 days (full year)
- **Columns**: 3
- **Key Fields**: Date, Offline_Spend, Online_Spend
- **Data Quality**: Daily marketing spend data for 2019

#### 5. Discount_Coupon (existing CSV)
- **Rows**: 204 coupon entries
- **Columns**: 4
- **Key Fields**: Month, Product_Category, Coupon_Code, Discount_pct
- **Data Quality**: Monthly coupon data across product categories

## Schema Analysis Results

### Key Insights:
1. **Customer Base**: 1,468 unique customers across 5 locations
2. **Transaction Volume**: 52,924 transactions with 25,061 unique transaction IDs
3. **Product Catalog**: 1,145 unique SKUs across 20 product categories
4. **Time Period**: Full year 2019 data (365 days)
5. **Revenue Potential**: Comprehensive pricing and quantity data available

### Data Relationships:
- CustomerID links CustomersData and Online_Sales tables
- Product_Category links Tax_amount, Discount_Coupon, and Online_Sales tables
- Transaction dates enable time-based analysis with Marketing_Spend data

## Files Generated

### 1. `convert_excel_to_csv.py`
Python script that:
- Converts Excel files to CSV format
- Analyzes schema of all CSV files
- Generates Snowflake DDL statements
- Provides data quality insights
- Saves schema information to JSON

### 2. `data_schemas.json`
Detailed schema information including:
- Column data types and null counts
- Suggested Snowflake data types
- Sample values for each column
- Data quality metrics

### 3. `snowflake_ingestion_script.sql`
Complete Snowflake ingestion script with:
- File format creation for CSV parsing
- Table DDL statements optimized for Snowflake
- COPY INTO commands for data loading
- Data validation queries
- Sample analytics queries

### 4. `requirements.txt`
Python dependencies for the conversion script

## Snowflake Table Structures

### CUSTOMERSDATA
```sql
CREATE TABLE CUSTOMERSDATA (
    CUSTOMERID NUMBER NOT NULL,
    GENDER VARCHAR(1) NOT NULL,
    LOCATION VARCHAR(13) NOT NULL,
    TENURE_MONTHS NUMBER NOT NULL
);
```

### TAX_AMOUNT
```sql
CREATE TABLE TAX_AMOUNT (
    PRODUCT_CATEGORY VARCHAR(20) NOT NULL,
    GST FLOAT NOT NULL
);
```

### ONLINE_SALES
```sql
CREATE TABLE ONLINE_SALES (
    CUSTOMERID NUMBER NOT NULL,
    TRANSACTION_ID NUMBER NOT NULL,
    TRANSACTION_DATE VARCHAR(10) NOT NULL,
    PRODUCT_SKU VARCHAR(14) NOT NULL,
    PRODUCT_DESCRIPTION VARCHAR(59) NOT NULL,
    PRODUCT_CATEGORY VARCHAR(20) NOT NULL,
    QUANTITY NUMBER NOT NULL,
    AVG_PRICE FLOAT NOT NULL,
    DELIVERY_CHARGES FLOAT NOT NULL,
    COUPON_STATUS VARCHAR(8) NOT NULL
);
```

### MARKETING_SPEND
```sql
CREATE TABLE MARKETING_SPEND (
    DATE VARCHAR(10) NOT NULL,
    OFFLINE_SPEND NUMBER NOT NULL,
    ONLINE_SPEND FLOAT NOT NULL
);
```

### DISCOUNT_COUPON
```sql
CREATE TABLE DISCOUNT_COUPON (
    MONTH VARCHAR(3) NOT NULL,
    PRODUCT_CATEGORY VARCHAR(20) NOT NULL,
    COUPON_CODE VARCHAR(7) NOT NULL,
    DISCOUNT_PCT NUMBER NOT NULL
);
```

## Next Steps for Snowflake Ingestion

### 1. Environment Setup
- Create Snowflake database and schema
- Set up appropriate user roles and permissions
- Configure warehouse for data loading

### 2. File Upload
- Upload CSV files to Snowflake stage (internal or external S3)
- Verify file accessibility and format

### 3. Execute Ingestion Script
- Run `snowflake_ingestion_script.sql`
- Monitor data load progress and error handling
- Validate row counts match expected values

### 4. Data Validation
- Execute validation queries provided in the script
- Check data consistency across related tables
- Verify date formats and ranges

### 5. Post-Ingestion Optimization
- Create indexes on frequently queried columns
- Set up primary and foreign key constraints
- Consider clustering keys for large tables (Online_Sales)
- Implement data retention policies

## Data Quality Considerations

### Potential Issues to Monitor:
1. **Date Formats**: Currently stored as VARCHAR(10) - consider converting to DATE type
2. **Product Categories**: Ensure consistency across all tables (20 categories identified)
3. **Customer IDs**: Verify referential integrity between CustomersData and Online_Sales
4. **Transaction IDs**: Some transactions may have multiple line items (not unique per row)

### Recommendations:
1. Convert date columns to proper DATE/TIMESTAMP types during transformation
2. Implement data quality checks in your ELT pipeline
3. Consider creating a dimensional model for better analytics performance
4. Set up monitoring for data freshness and completeness

## Usage

### Running the Conversion Script:
```bash
pip install -r requirements.txt
python convert_excel_to_csv.py
```

### Loading into Snowflake:
1. Update database/schema names in `snowflake_ingestion_script.sql`
2. Upload CSV files to your Snowflake stage
3. Execute the SQL script in Snowflake

## File Sizes and Performance Notes
- **Online_Sales.csv**: 5.0MB (largest file) - consider partitioning strategies
- **CustomersData.csv**: 30KB - small lookup table
- **Other files**: < 10KB each - minimal performance impact

Total data volume is manageable for initial ingestion, but consider partitioning strategies as data grows.
