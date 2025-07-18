# Semantic Layer for Marketing Insight Pipeline
# Defines table structures, metrics, and dimensions for AI agent queries

fct_sales_semantic = {
    "table": "fct_sales",
    "description": "Sales fact table with calculated financial metrics",
    "metrics": {
        "total_net_sales": "SUM(net_sales_amount)",
        "total_gross_sales": "SUM(gross_sales_amount)",
        "total_quantity": "SUM(quantity)",
        "average_discount": "AVG(discount_percentage)",
        "total_gst": "SUM(gst_amount)",
        "total_delivery_charges": "SUM(delivery_charges)",
        "average_order_value": "AVG(total_amount)",
        "total_discount_amount": "SUM(discount_amount)",
        "transaction_count": "COUNT(DISTINCT transaction_id)"
    },
    "dimensions": {
        "sale_size_category": "sale_size_category",
        "month": "TO_CHAR(transaction_date, 'YYYY-MM')",
        "year": "EXTRACT(YEAR FROM transaction_date)",
        "quarter": "TO_CHAR(transaction_date, 'YYYY-Q')",
        "transaction_date": "transaction_date",
        "customer_id": "customer_id",
        "product_sku": "product_sku",
        "coupon_status": "coupon_status"
    },
    "date_column": "transaction_date",
    "primary_key": "transaction_id"
}

# Additional semantic models can be added here
fct_customer_segments_semantic = {
    "table": "fct_customer_segments",
    "description": "Customer segmentation facts with ML-driven segments and business metrics",
    "metrics": {
        "total_customers": "COUNT(DISTINCT customer_id)",
        "avg_revenue_per_customer": "AVG(total_revenue)",
        "avg_order_count": "AVG(total_orders)",
        "avg_days_since_purchase": "AVG(days_since_last_purchase)"
    },
    "dimensions": {
        "segment_name": "segment_name",
        "segment_id": "segment_id",
        "activity_status": "activity_status",
        "location": "location",
        "gender": "gender"
    },
    "date_column": "updated_at",
    "primary_key": "customer_id"
}

dim_products_semantic = {
    "table": "dim_products",
    "description": "Product dimension table with product groups and tax information",
    "metrics": {
        "product_count": "COUNT(DISTINCT product_sku)",
        "avg_gst_rate": "AVG(gst_rate)"
    },
    "dimensions": {
        "product_group": "product_group",
        "product_category": "product_category",
        "product_sku": "product_sku"
    },
    "primary_key": "product_sku"
}

# Registry of all available semantic models
SEMANTIC_MODELS = {
    "fct_sales": fct_sales_semantic,
    "fct_customer_segments": fct_customer_segments_semantic,
    "dim_products": dim_products_semantic
}
