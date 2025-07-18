"""
LangChain Tools for Snowflake Query Execution
Provides tools for the LangGraph agent to query Snowflake data
"""

from langchain_core.tools import tool
from typing import Optional, Dict, Any, List
import json
import logging
from ..utils.snowflake_client import create_snowflake_client
from .sql_builder import build_sales_query, build_generic_query, get_available_metrics, get_available_dimensions

# Configure logging
logger = logging.getLogger(__name__)

# Snowflake client will be initialized lazily when first needed
snowflake_client = None

def get_snowflake_client():
    """Get or create Snowflake client instance"""
    global snowflake_client
    if snowflake_client is None:
        try:
            snowflake_client = create_snowflake_client()
        except Exception as e:
            logger.warning(f"Snowflake client initialization failed: {e}")
            snowflake_client = None
    return snowflake_client


@tool
def run_sales_query(
    metric: str,
    group_by: str = "",
    start_date: str = "",
    end_date: str = "",
    month: str = "",
    additional_filters: str = ""
) -> str:
    """
    Execute a query on the fct_sales table to get sales metrics.

    Args:
        metric: The metric to calculate (e.g., 'total_net_sales', 'total_gross_sales', 'average_discount')
        group_by: Dimension to group by (e.g., 'month', 'sale_size_category', 'customer_id')
        start_date: Start date filter in YYYY-MM-DD format (optional)
        end_date: End date filter in YYYY-MM-DD format (optional)
        month: Month filter in YYYY-MM format (optional, alternative to start_date/end_date)
        additional_filters: JSON string of additional filters (optional)

    Returns:
        String containing the query results and executed SQL
        """
    client = get_snowflake_client()
    if not client:
        return "Error: Snowflake client not configured. Please check connection settings."

    try:
        # Parse additional filters if provided
        filters = None
        if additional_filters:
            try:
                filters = json.loads(additional_filters)
            except json.JSONDecodeError:
                return f"Error: Invalid JSON format in additional_filters: {additional_filters}"

        # Build the SQL query
        query = build_sales_query(
            metric=metric,
            group_by=group_by if group_by else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            month=month if month else None,
            filters=filters
        )

        # Check if query generation failed
        if query.startswith("Error:"):
            return query

        # Execute the query
        results = client.execute_query(query)

        # Format results
        if not results:
            return f"Query executed successfully but returned no results.\n\nExecuted query:\n{query}"

        # Convert results to readable format
        result_lines = []
        for row in results[:20]:  # Limit to first 20 results
            result_lines.append(str(dict(row)))

        result_summary = f"Found {len(results)} result(s). Showing first {min(len(results), 20)}:\n"
        result_summary += "\n".join(result_lines)

        if len(results) > 20:
            result_summary += f"\n... and {len(results) - 20} more results"

        return f"Query executed successfully!\n\nExecuted query:\n{query}\n\nResults:\n{result_summary}"

    except Exception as e:
        logger.error(f"Error executing sales query: {str(e)}")
        return f"Error executing query: {str(e)}"


@tool
def run_generic_query(
    table_name: str,
    metric: str,
    group_by: str = "",
    start_date: str = "",
    end_date: str = "",
    additional_filters: str = "",
    limit: int = 100
) -> str:
    """
    Execute a query on any available table using the semantic model.

    Args:
        table_name: Name of the table (e.g., 'fct_sales', 'fct_customer_segments', 'dim_products')
        metric: The metric to calculate
        group_by: Dimension to group by (optional)
        start_date: Start date filter in YYYY-MM-DD format (optional)
        end_date: End date filter in YYYY-MM-DD format (optional)
        additional_filters: JSON string of additional filters (optional)
        limit: Maximum number of results to return (default 100)

    Returns:
        String containing the query results and executed SQL
        """
    client = get_snowflake_client()
    if not client:
        return "Error: Snowflake client not configured. Please check connection settings."

    try:
        # Parse additional filters if provided
        filters = None
        if additional_filters:
            try:
                filters = json.loads(additional_filters)
            except json.JSONDecodeError:
                return f"Error: Invalid JSON format in additional_filters: {additional_filters}"

        # Build the SQL query
        query = build_generic_query(
            table_name=table_name,
            metric=metric,
            group_by=group_by if group_by else None,
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            filters=filters,
            limit=limit
        )

        # Check if query generation failed
        if query.startswith("Error:"):
            return query

        # Execute the query
        results = client.execute_query(query)

        # Format results
        if not results:
            return f"Query executed successfully but returned no results.\n\nExecuted query:\n{query}"

        # Convert results to readable format
        result_lines = []
        for row in results[:20]:  # Limit display to first 20 results
            result_lines.append(str(dict(row)))

        result_summary = f"Found {len(results)} result(s). Showing first {min(len(results), 20)}:\n"
        result_summary += "\n".join(result_lines)

        if len(results) > 20:
            result_summary += f"\n... and {len(results) - 20} more results"

        return f"Query executed successfully!\n\nExecuted query:\n{query}\n\nResults:\n{result_summary}"

    except Exception as e:
        logger.error(f"Error executing generic query: {str(e)}")
        return f"Error executing query: {str(e)}"


@tool
def get_table_schema_info(table_name: str) -> str:
    """
    Get schema information for a table including available metrics and dimensions.

    Args:
        table_name: Name of the table

    Returns:
        String containing table schema information
    """
    try:
        metrics = get_available_metrics(table_name)
        dimensions = get_available_dimensions(table_name)

        if not metrics and not dimensions:
            return f"Table '{table_name}' not found in semantic models. Available tables: fct_sales, fct_customer_segments, dim_products"

        schema_info = f"Schema information for {table_name}:\n\n"
        schema_info += f"Available Metrics:\n{chr(10).join(f'- {metric}' for metric in metrics)}\n\n"
        schema_info += f"Available Dimensions:\n{chr(10).join(f'- {dimension}' for dimension in dimensions)}\n"

        return schema_info

    except Exception as e:
        return f"Error getting schema info: {str(e)}"


@tool
def test_snowflake_connection() -> str:
    """
    Test the Snowflake database connection.

    Returns:
        String indicating connection status
        """
    client = get_snowflake_client()
    if not client:
        return "Error: Snowflake client not configured. Please check connection settings."

    try:
        if client.test_connection():
            return "Snowflake connection test successful!"
        else:
            return "Snowflake connection test failed."
    except Exception as e:
        return f"Connection test error: {str(e)}"


# Export all tools for easy import
__all__ = [
    'run_sales_query',
    'run_generic_query',
    'get_table_schema_info',
    'test_snowflake_connection'
]
