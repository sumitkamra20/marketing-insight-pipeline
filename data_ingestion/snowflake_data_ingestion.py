#!/usr/bin/env python3
"""
Snowflake Data Ingestion Script
This script reads table schemas and automatically ingests CSV data into Snowflake tables.
"""

import snowflake.connector
import pandas as pd
import json
import os
from pathlib import Path
import sys
from typing import Dict, Any, List
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('snowflake_ingestion.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SnowflakeDataIngestion:
    def __init__(self, config_file: str = "snowflake_config.json"):
        """
        Initialize Snowflake connection and load configuration.

        Args:
            config_file: Path to Snowflake configuration file
        """
        self.config = self.load_config(config_file)
        self.connection = None
        self.cursor = None
        self.schemas = self.load_table_schemas()
        self.data_dir = "../data/raw"

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load Snowflake configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"✓ Loaded configuration from {config_file}")
            return config
        except FileNotFoundError:
            logger.warning(f"Configuration file {config_file} not found. Creating template...")
            self.create_config_template(config_file)
            raise FileNotFoundError(f"Please update {config_file} with your Snowflake credentials")

    def create_config_template(self, config_file: str):
        """Create a template configuration file."""
        template = {
            "account": "your-account.snowflakecomputing.com",
            "user": "your-username",
            "password": "your-password",
            "warehouse": "your-warehouse",
            "database": "your-database",
            "schema": "your-schema",
            "role": "your-role"
        }
        with open(config_file, 'w') as f:
            json.dump(template, f, indent=2)
        logger.info(f"Created configuration template: {config_file}")

    def load_table_schemas(self) -> Dict[str, Any]:
        """Load table schemas from JSON file."""
        try:
            with open("table_schemas.json", 'r') as f:
                schemas = json.load(f)
            logger.info(f"✓ Loaded schemas for {len(schemas)} tables")
            return schemas
        except FileNotFoundError:
            logger.error("table_schemas.json not found. Run data_conversion_and_schema.py first.")
            raise

    def connect_to_snowflake(self):
        """Establish connection to Snowflake."""
        try:
            self.connection = snowflake.connector.connect(
                account=self.config['account'],
                user=self.config['user'],
                password=self.config['password'],
                warehouse=self.config['warehouse'],
                database=self.config['database'],
                schema=self.config['schema'],
                role=self.config.get('role')
            )
            self.cursor = self.connection.cursor()
            logger.info(f"✓ Connected to Snowflake: {self.config['database']}.{self.config['schema']}")

            # Test connection
            self.cursor.execute("SELECT CURRENT_VERSION()")
            version = self.cursor.fetchone()[0]
            logger.info(f"✓ Snowflake version: {version}")

        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {str(e)}")
            raise

    def create_tables(self):
        """Create all tables based on schema definitions."""
        logger.info("🔨 Creating Snowflake tables...")

        for table_name, schema_info in self.schemas.items():
            try:
                ddl = self.generate_ddl(schema_info)
                logger.info(f"Creating table: {schema_info['table_name']}")
                self.cursor.execute(ddl)
                logger.info(f"✓ Created table {schema_info['table_name']}")
            except Exception as e:
                logger.error(f"Failed to create table {schema_info['table_name']}: {str(e)}")
                raise

    def generate_ddl(self, schema_info: Dict[str, Any]) -> str:
        """Generate DDL statement from schema information."""
        table_name = schema_info['table_name']
        ddl = f"CREATE OR REPLACE TABLE {table_name} (\n"

        columns = []
        for col_name, col_info in schema_info['columns'].items():
            clean_col_name = col_info['column_name']
            nullable = "NULL" if col_info['null_count'] > 0 else "NOT NULL"
            columns.append(f"    {clean_col_name} {col_info['snowflake_type']} {nullable}")

        ddl += ",\n".join(columns)
        ddl += "\n);"

        return ddl

    def create_file_format(self):
        """Create CSV file format for data loading."""
        file_format_sql = """
        CREATE OR REPLACE FILE FORMAT csv_format
            TYPE = 'CSV'
            FIELD_DELIMITER = ','
            RECORD_DELIMITER = '\\n'
            SKIP_HEADER = 1
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            TRIM_SPACE = TRUE
            ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
            ESCAPE = 'NONE'
            ESCAPE_UNENCLOSED_FIELD = '\\\\'
            DATE_FORMAT = 'AUTO'
            TIMESTAMP_FORMAT = 'AUTO'
        """

        try:
            self.cursor.execute(file_format_sql)
            logger.info("✓ Created CSV file format")
        except Exception as e:
            logger.error(f"Failed to create file format: {str(e)}")
            raise

    def create_stage(self, stage_name: str = "csv_stage"):
        """Create internal stage for file uploads."""
        stage_sql = f"CREATE OR REPLACE STAGE {stage_name}"

        try:
            self.cursor.execute(stage_sql)
            logger.info(f"✓ Created stage: {stage_name}")
        except Exception as e:
            logger.error(f"Failed to create stage: {str(e)}")
            raise

    def upload_files_to_stage(self, stage_name: str = "csv_stage"):
        """Upload CSV files to Snowflake stage."""
        logger.info("📤 Uploading CSV files to Snowflake stage...")

        csv_files = list(Path(self.data_dir).glob("*.csv"))

        for csv_file in csv_files:
            try:
                put_sql = f"PUT file://{csv_file.absolute()} @{stage_name}/"
                self.cursor.execute(put_sql)
                logger.info(f"✓ Uploaded {csv_file.name}")
            except Exception as e:
                logger.error(f"Failed to upload {csv_file.name}: {str(e)}")
                raise

    def load_data_to_tables(self, stage_name: str = "csv_stage"):
        """Load data from stage to tables using COPY INTO."""
        logger.info("📥 Loading data into Snowflake tables...")

        for table_name, schema_info in self.schemas.items():
            csv_filename = f"{table_name}.csv"
            table_name_upper = schema_info['table_name']

            copy_sql = f"""
            COPY INTO {table_name_upper}
            FROM @{stage_name}/{csv_filename}
            FILE_FORMAT = (FORMAT_NAME = csv_format)
            ON_ERROR = 'ABORT_STATEMENT'
            """

            try:
                self.cursor.execute(copy_sql)
                result = self.cursor.fetchall()

                # Get load statistics
                if result:
                    rows_loaded = result[0][1] if len(result[0]) > 1 else "Unknown"
                    logger.info(f"✓ Loaded {rows_loaded} rows into {table_name_upper}")
                else:
                    logger.info(f"✓ Data loaded into {table_name_upper}")

            except Exception as e:
                logger.error(f"Failed to load data into {table_name_upper}: {str(e)}")
                raise

    def validate_data_loads(self):
        """Validate that data was loaded correctly."""
        logger.info("🔍 Validating data loads...")

        validation_results = {}

        for table_name, schema_info in self.schemas.items():
            table_name_upper = schema_info['table_name']
            expected_rows = schema_info['total_rows']

            try:
                # Count rows in Snowflake table
                count_sql = f"SELECT COUNT(*) FROM {table_name_upper}"
                self.cursor.execute(count_sql)
                actual_rows = self.cursor.fetchone()[0]

                validation_results[table_name_upper] = {
                    'expected_rows': expected_rows,
                    'actual_rows': actual_rows,
                    'match': expected_rows == actual_rows
                }

                status = "✓" if expected_rows == actual_rows else "⚠️"
                logger.info(f"{status} {table_name_upper}: {actual_rows}/{expected_rows} rows")

            except Exception as e:
                logger.error(f"Failed to validate {table_name_upper}: {str(e)}")
                validation_results[table_name_upper] = {
                    'expected_rows': expected_rows,
                    'actual_rows': 0,
                    'match': False,
                    'error': str(e)
                }

        return validation_results

    def run_data_quality_checks(self):
        """Run additional data quality checks."""
        logger.info("🔎 Running data quality checks...")

        quality_checks = {
            'customer_referential_integrity': """
                SELECT COUNT(*) as orphaned_sales
                FROM ONLINE_SALES os
                LEFT JOIN CUSTOMERSDATA cd ON os.CUSTOMERID = cd.CUSTOMERID
                WHERE cd.CUSTOMERID IS NULL
            """,
            'product_category_consistency': """
                SELECT DISTINCT os.PRODUCT_CATEGORY
                FROM ONLINE_SALES os
                WHERE os.PRODUCT_CATEGORY NOT IN (
                    SELECT PRODUCT_CATEGORY FROM TAX_AMOUNT
                )
            """,
            'date_range_check': """
                SELECT
                    MIN(TRANSACTION_DATE) as min_date,
                    MAX(TRANSACTION_DATE) as max_date,
                    COUNT(DISTINCT TRANSACTION_DATE) as unique_dates
                FROM ONLINE_SALES
            """
        }

        for check_name, sql in quality_checks.items():
            try:
                self.cursor.execute(sql)
                result = self.cursor.fetchall()
                logger.info(f"✓ {check_name}: {result}")
            except Exception as e:
                logger.error(f"Failed quality check {check_name}: {str(e)}")

    def generate_summary_report(self):
        """Generate a summary report of the ingestion."""
        logger.info("📊 Generating ingestion summary...")

        summary_sql = """
        SELECT 'CUSTOMERSDATA' as table_name, COUNT(*) as row_count FROM CUSTOMERSDATA
        UNION ALL
        SELECT 'TAX_AMOUNT' as table_name, COUNT(*) as row_count FROM TAX_AMOUNT
        UNION ALL
        SELECT 'MARKETING_SPEND' as table_name, COUNT(*) as row_count FROM MARKETING_SPEND
        UNION ALL
        SELECT 'DISCOUNT_COUPON' as table_name, COUNT(*) as row_count FROM DISCOUNT_COUPON
        UNION ALL
        SELECT 'ONLINE_SALES' as table_name, COUNT(*) as row_count FROM ONLINE_SALES
        ORDER BY row_count DESC
        """

        try:
            self.cursor.execute(summary_sql)
            results = self.cursor.fetchall()

            logger.info("\n" + "="*60)
            logger.info("SNOWFLAKE INGESTION SUMMARY")
            logger.info("="*60)

            total_rows = 0
            for table_name, row_count in results:
                logger.info(f"{table_name:<20} {row_count:>10,} rows")
                total_rows += row_count

            logger.info("-"*60)
            logger.info(f"{'TOTAL':<20} {total_rows:>10,} rows")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"Failed to generate summary: {str(e)}")

    def close_connection(self):
        """Close Snowflake connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("✓ Closed Snowflake connection")

    def run_full_ingestion(self):
        """Run the complete data ingestion process."""
        start_time = datetime.now()
        logger.info("🚀 Starting Snowflake Data Ingestion")
        logger.info("="*60)

        try:
            # Step 1: Connect to Snowflake
            self.connect_to_snowflake()

            # Step 2: Create file format and stage
            self.create_file_format()
            self.create_stage()

            # Step 3: Create tables
            self.create_tables()

            # Step 4: Upload files to stage
            self.upload_files_to_stage()

            # Step 5: Load data into tables
            self.load_data_to_tables()

            # Step 6: Validate data loads
            validation_results = self.validate_data_loads()

            # Step 7: Run data quality checks
            self.run_data_quality_checks()

            # Step 8: Generate summary report
            self.generate_summary_report()

            end_time = datetime.now()
            duration = end_time - start_time

            logger.info(f"\n✅ Ingestion completed successfully!")
            logger.info(f"⏱️  Total time: {duration}")
            logger.info(f"📁 Ingested {len(self.schemas)} tables")

            # Check if all validations passed
            all_valid = all(result['match'] for result in validation_results.values())
            if all_valid:
                logger.info("🎉 All data validation checks passed!")
            else:
                logger.warning("⚠️  Some data validation checks failed. Please review.")

        except Exception as e:
            logger.error(f"❌ Ingestion failed: {str(e)}")
            raise
        finally:
            self.close_connection()

def main():
    """Main function to run data ingestion."""
    try:
        ingestion = SnowflakeDataIngestion()
        ingestion.run_full_ingestion()
    except Exception as e:
        logger.error(f"Failed to run ingestion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
