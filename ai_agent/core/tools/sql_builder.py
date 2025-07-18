"""
SQL Builder Tool for Marketing Insight Pipeline
Generates SQL queries based on semantic model definitions
"""

from typing import Optional, List, Dict, Any
from ..semantic_model import SEMANTIC_MODELS, fct_sales_semantic


def build_sales_query(
    metric: str,
    group_by: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    month: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build SQL query for fct_sales table based on semantic model

    Args:
        metric: The metric to calculate (e.g., 'total_net_sales')
        group_by: Dimension to group by (e.g., 'month', 'sale_size_category')
        start_date: Start date filter (YYYY-MM-DD format)
        end_date: End date filter (YYYY-MM-DD format)
        month: Month filter (YYYY-MM format)
        filters: Additional filters as key-value pairs

    Returns:
        SQL query string
    """
    semantic_model = fct_sales_semantic
    table = semantic_model["table"]

    # Get metric expression
    metric_expr = semantic_model["metrics"].get(metric)
    if not metric_expr:
        available_metrics = list(semantic_model["metrics"].keys())
        return f"Error: Metric '{metric}' not supported. Available metrics: {available_metrics}"

    # Get group by expression
    group_expr = None
    if group_by:
        group_expr = semantic_model["dimensions"].get(group_by, group_by)

    # Build SELECT clause
    select_parts = []
    if group_expr:
        select_parts.append(f"{group_expr} AS {group_by}")
    select_parts.append(f"{metric_expr} AS {metric}")
    select_clause = "SELECT " + ", ".join(select_parts)

    # Build WHERE clause
    where_clauses = []
    date_column = semantic_model["date_column"]

    if start_date and end_date:
        where_clauses.append(f"{date_column} BETWEEN '{start_date}' AND '{end_date}'")
    elif month:
        where_clauses.append(f"TO_CHAR({date_column}, 'YYYY-MM') = '{month}'")

    # Add additional filters
    if filters:
        for column, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{column} = '{value}'")
            elif isinstance(value, list):
                value_list = "', '".join(str(v) for v in value)
                where_clauses.append(f"{column} IN ('{value_list}')")
            else:
                where_clauses.append(f"{column} = {value}")

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Build GROUP BY clause
    group_clause = f"GROUP BY {group_expr}" if group_expr else ""

    # Build ORDER BY clause
    order_clause = f"ORDER BY {group_expr}" if group_expr else ""

    # Construct final query
    query_parts = [
        select_clause,
        f"FROM {table}",
        where_clause,
        group_clause,
        order_clause
    ]

    query = "\n".join(part for part in query_parts if part)
    return query


def build_generic_query(
    table_name: str,
    metric: str,
    group_by: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
    limit: Optional[int] = None
) -> str:
    """
    Build SQL query for any table using semantic models

    Args:
        table_name: Name of the table (must be in SEMANTIC_MODELS)
        metric: The metric to calculate
        group_by: Dimension to group by
        start_date: Start date filter
        end_date: End date filter
        filters: Additional filters
        limit: Limit number of results

    Returns:
        SQL query string
    """
    if table_name not in SEMANTIC_MODELS:
        available_tables = list(SEMANTIC_MODELS.keys())
        return f"Error: Table '{table_name}' not found. Available tables: {available_tables}"

    semantic_model = SEMANTIC_MODELS[table_name]
    table = semantic_model["table"]

    # Get metric expression
    metric_expr = semantic_model["metrics"].get(metric)
    if not metric_expr:
        available_metrics = list(semantic_model["metrics"].keys())
        return f"Error: Metric '{metric}' not supported for {table_name}. Available metrics: {available_metrics}"

    # Get group by expression
    group_expr = None
    if group_by:
        group_expr = semantic_model["dimensions"].get(group_by, group_by)

    # Build SELECT clause
    select_parts = []
    if group_expr:
        select_parts.append(f"{group_expr} AS {group_by}")
    select_parts.append(f"{metric_expr} AS {metric}")
    select_clause = "SELECT " + ", ".join(select_parts)

    # Build WHERE clause
    where_clauses = []

    # Add date filters if date column exists
    if "date_column" in semantic_model and start_date and end_date:
        date_column = semantic_model["date_column"]
        where_clauses.append(f"{date_column} BETWEEN '{start_date}' AND '{end_date}'")

    # Add additional filters
    if filters:
        for column, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{column} = '{value}'")
            elif isinstance(value, list):
                value_list = "', '".join(str(v) for v in value)
                where_clauses.append(f"{column} IN ('{value_list}')")
            else:
                where_clauses.append(f"{column} = {value}")

    where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Build GROUP BY clause
    group_clause = f"GROUP BY {group_expr}" if group_expr else ""

    # Build ORDER BY clause
    order_clause = f"ORDER BY {group_expr}" if group_expr else ""

    # Build LIMIT clause
    limit_clause = f"LIMIT {limit}" if limit else ""

    # Construct final query
    query_parts = [
        select_clause,
        f"FROM {table}",
        where_clause,
        group_clause,
        order_clause,
        limit_clause
    ]

    query = "\n".join(part for part in query_parts if part)
    return query


def get_available_metrics(table_name: str) -> List[str]:
    """Get list of available metrics for a table"""
    if table_name in SEMANTIC_MODELS:
        return list(SEMANTIC_MODELS[table_name]["metrics"].keys())
    return []


def get_available_dimensions(table_name: str) -> List[str]:
    """Get list of available dimensions for a table"""
    if table_name in SEMANTIC_MODELS:
        return list(SEMANTIC_MODELS[table_name]["dimensions"].keys())
    return []


def get_table_description(table_name: str) -> str:
    """Get description of a table"""
    if table_name in SEMANTIC_MODELS:
        return SEMANTIC_MODELS[table_name].get("description", "No description available")
    return f"Table '{table_name}' not found"
