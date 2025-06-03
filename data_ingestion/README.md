# Data Ingestion Scripts

This folder contains the data ingestion scripts for the Marketing Insight Pipeline ELT process.

## Files

- **`data_conversion_and_schema.py`** - Convert Excel files to CSV, load data into pandas dataframes, and analyze schemas
- **`snowflake_data_ingestion.py`** - Automated Python script for Snowflake data ingestion
- **`snowflake_ingestion_script.sql`** - Manual SQL script for Snowflake table creation and data loading
- **`run_ingestion.py`** - Simple CLI to run ingestion tasks
- **`snowflake_config_template.json`** - Template for Snowflake configuration
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation file

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Snowflake Configuration
```bash
# Copy template and update with your credentials
cp snowflake_config_template.json snowflake_config.json
# Edit snowflake_config.json with your Snowflake details
```

### 3. Run Complete Pipeline
```bash
# Option A: Run everything in one command
python run_ingestion.py all

# Option B: Run step by step
python run_ingestion.py convert    # Convert Excel + analyze schemas
python run_ingestion.py ingest     # Load to Snowflake
```

## Detailed Usage

### Data Conversion and Schema Analysis
```bash
python data_conversion_and_schema.py
```

This script will:
- Convert Excel files (.xls/.xlsx) from `../data/raw/` to CSV format
- Load all CSV files into pandas dataframes for analysis
- Analyze schemas of all dataframes for Snowflake table design
- Generate clean Snowflake DDL statements with proper data types
- Create a `table_schemas.json` file with detailed schema information
- Provide visual schema summary with null indicators and unique value counts

### Snowflake Data Ingestion (Python - Recommended)

#### Setup Configuration
1. Copy the template: `cp snowflake_config_template.json snowflake_config.json`
2. Update `snowflake_config.json` with your Snowflake credentials:
```json
{
  "account": "your-account.snowflakecomputing.com",
  "user": "your-username",
  "password": "your-password",
  "warehouse": "your-warehouse",
  "database": "your-database",
  "schema": "your-schema",
  "role": "your-role"
}
```

#### Run Ingestion
```bash
python snowflake_data_ingestion.py
```

The Python script will:
- ✅ Connect to Snowflake using your configuration
- ✅ Create CSV file format and internal stage
- ✅ Create all tables based on `table_schemas.json`
- ✅ Upload CSV files to Snowflake stage
- ✅ Load data using optimized COPY INTO commands
- ✅ Validate row counts match expected values
- ✅ Run data quality checks (referential integrity, etc.)
- ✅ Generate comprehensive ingestion summary
- ✅ Create detailed logs in `snowflake_ingestion.log`

### Manual Snowflake Ingestion (SQL)
1. Update database and schema names in `snowflake_ingestion_script.sql`
2. Upload CSV files to your Snowflake stage manually
3. Execute the SQL script in Snowflake

## Why Choose Python over Manual SQL?

### ✅ **Python Approach (Recommended)**
- **Automated**: Entire process runs with one command
- **Error Handling**: Comprehensive error handling and logging
- **Validation**: Automatic data validation and quality checks
- **Flexible**: Easy to customize and integrate with other systems
- **Monitoring**: Detailed logging and progress tracking
- **Schema-Driven**: Reads your `table_schemas.json` automatically

### 📝 **Manual SQL Approach**
- **Control**: Fine-grained control over each step
- **Learning**: Good for understanding Snowflake mechanics
- **Custom**: Easy to modify SQL for specific requirements

## Your Data Summary

Based on your `table_schemas.json`, the ingestion will process:

| Table | Rows | Columns | Key Features |
|-------|------|---------|--------------|
| ONLINE_SALES | 52,924 | 10 | Main transaction table |
| CUSTOMERSDATA | 1,468 | 4 | Customer master data |
| MARKETING_SPEND | 365 | 3 | Daily marketing spend |
| DISCOUNT_COUPON | 204 | 4 | Coupon definitions |
| TAX_AMOUNT | 20 | 2 | Product category tax rates |

**Total: 54,981 rows across 5 tables**

## Advanced Features

### Interactive Usage
```python
from data_conversion_and_schema import DataConversionAndSchema
from snowflake_data_ingestion import SnowflakeDataIngestion

# Data analysis
analyzer = DataConversionAndSchema()
analyzer.run_full_analysis()

# Access dataframes
customers_df = analyzer.dataframes['CustomersData']
sales_df = analyzer.dataframes['Online_Sales']

# Snowflake ingestion
ingestion = SnowflakeDataIngestion()
ingestion.run_full_ingestion()
```

### Custom Configuration
```bash
# Use custom config file
python run_ingestion.py ingest --config my_snowflake_config.json
```

### Logging and Monitoring
- All operations are logged to `snowflake_ingestion.log`
- Console output provides real-time progress
- Detailed error messages for troubleshooting

## Data Quality Checks

The Python script automatically runs these quality checks:

1. **Row Count Validation**: Ensures all expected rows are loaded
2. **Referential Integrity**: Checks customer ID relationships
3. **Product Category Consistency**: Validates categories across tables
4. **Date Range Analysis**: Analyzes transaction date patterns

## Troubleshooting

### Common Issues

1. **Configuration Error**
   ```
   Copy snowflake_config_template.json to snowflake_config.json and update credentials
   ```

2. **Missing Schema File**
   ```
   Run data_conversion_and_schema.py first to generate table_schemas.json
   ```

3. **Connection Issues**
   ```
   Verify your Snowflake account URL, username, and password
   Check if your warehouse is running
   ```

4. **Permission Issues**
   ```
   Ensure your user has CREATE TABLE, CREATE STAGE, and INSERT permissions
   ```

## Output Files

After running the scripts, you'll find:
- **`table_schemas.json`** - Complete schema analysis
- **`snowflake_ingestion.log`** - Detailed ingestion logs
- **Converted CSV files** in `../data/raw/`
- **All dataframes** accessible via the analyzer object

## Next Steps

1. Run the ingestion scripts to load your data
2. Use the loaded Snowflake tables in your dbt transformations
3. Set up automated scheduling using tools like Airflow or cron
4. Monitor data quality using the built-in validation checks
