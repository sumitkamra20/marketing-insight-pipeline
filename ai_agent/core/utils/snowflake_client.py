"""
Snowflake Client Utility for Marketing Insight Pipeline
Handles database connections and query execution
"""

import snowflake.connector
from snowflake.connector import DictCursor
import pandas as pd
from typing import List, Dict, Any, Optional
import os
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SnowflakeClient:
    """Snowflake database client for executing queries"""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize Snowflake client with connection parameters

        Args:
            config: Dictionary with connection parameters, if None uses environment variables
        """
        if config:
            self.config = config
        else:
            # Load from environment variables
            self.config = {
                'user': os.getenv('SNOWFLAKE_USER'),
                'password': os.getenv('SNOWFLAKE_PASSWORD'),
                'account': os.getenv('SNOWFLAKE_ACCOUNT'),
                'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE'),
                'database': os.getenv('SNOWFLAKE_DATABASE'),
                'schema': os.getenv('SNOWFLAKE_SCHEMA'),
                'role': os.getenv('SNOWFLAKE_ROLE', 'PUBLIC')
            }

        # Validate required parameters
        required_params = ['user', 'password', 'account', 'warehouse', 'database', 'schema']
        missing_params = [param for param in required_params if not self.config.get(param)]
        if missing_params:
            raise ValueError(f"Missing required Snowflake parameters: {missing_params}")

    @contextmanager
    def get_connection(self):
        """Context manager for Snowflake connections"""
        conn = None
        try:
            conn = snowflake.connector.connect(**self.config)
            yield conn
        except Exception as e:
            logger.error(f"Snowflake connection error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries

        Args:
            query: SQL query string

        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(DictCursor)
                logger.info(f"Executing query: {query[:100]}...")
                cursor.execute(query)
                results = cursor.fetchall()
                cursor.close()
                return results
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise

    def execute_query_df(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as pandas DataFrame

        Args:
            query: SQL query string

        Returns:
            pandas DataFrame with query results
        """
        try:
            with self.get_connection() as conn:
                logger.info(f"Executing query: {query[:100]}...")
                df = pd.read_sql(query, conn)
                return df
        except Exception as e:
            logger.error(f"Query execution error: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """
        Test the Snowflake connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                logger.info("Snowflake connection test successful")
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get column information for a table

        Args:
            table_name: Name of the table

        Returns:
            List of dictionaries with column information
        """
        query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = UPPER('{table_name}')
        AND table_schema = UPPER('{self.config["schema"]}')
        ORDER BY ordinal_position
        """
        return self.execute_query(query)

    def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get sample data from a table

        Args:
            table_name: Name of the table
            limit: Number of rows to return

        Returns:
            List of dictionaries with sample data
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)


def create_snowflake_client(config_path: Optional[str] = None) -> SnowflakeClient:
    """
    Factory function to create SnowflakeClient instance

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        SnowflakeClient instance
    """
    config = None
    if config_path:
        # Load configuration from file
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)

    return SnowflakeClient(config)
