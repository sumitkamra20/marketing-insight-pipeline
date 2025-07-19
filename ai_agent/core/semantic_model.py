# Semantic Layer for Marketing Insight Pipeline
# Defines table structures, metrics, and dimensions for AI agent queries

fct_sales_semantic = {
    "table": "fct_sales",
    "description": "Sales fact table with calculated financial metrics",
    "actual_columns": ["transaction_id", "customer_id", "transaction_date", "product_sku", "quantity",
                      "avg_price", "delivery_charges", "coupon_status", "gross_sales_amount",
                      "net_sales_amount", "gst_amount", "total_amount", "discount_percentage",
                      "discount_amount", "sale_size_category", "processed_at"],
    "metrics": {
        "total_net_sales": "SUM(net_sales_amount)",
        "total_gross_sales": "SUM(gross_sales_amount)",
        "total_quantity": "SUM(quantity)",
        "average_discount": "AVG(discount_percentage)",
        "total_gst": "SUM(gst_amount)",
        "total_delivery_charges": "SUM(delivery_charges)",
        "average_order_value": "AVG(total_amount)",
        "total_discount_amount": "SUM(discount_amount)",
        "transaction_count": "COUNT(DISTINCT transaction_id)",
        "total_revenue": "SUM(total_amount)"
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
    "aliases": {
        "customer_type": "customer_id",
        "product": "product_sku",
        "date": "transaction_date"
    },
    "date_column": "transaction_date",
    "primary_key": "transaction_id"
}

# Additional semantic models can be added here
fct_customer_segments_semantic = {
    "table": "fct_customer_segments",
    "description": "Customer segmentation facts with ML-driven segments and business metrics",
    "actual_columns": ["customer_id", "location", "gender", "customer_tenure_months", "segment_id",
                      "segment_name", "total_orders", "total_quantity", "total_revenue",
                      "first_purchase_date", "last_purchase_date", "days_since_last_purchase",
                      "customer_lifetime_days", "avg_order_value", "daily_revenue_rate",
                      "activity_status", "updated_at"],
    "metrics": {
        "total_customers": "COUNT(DISTINCT customer_id)",
        "avg_revenue_per_customer": "AVG(total_revenue)",
        "avg_order_count": "AVG(total_orders)",
        "avg_days_since_purchase": "AVG(days_since_last_purchase)",
        "customer_profitability": "AVG(total_revenue)",
        "total_customer_revenue": "SUM(total_revenue)"
    },
    "dimensions": {
        "segment_name": "segment_name",
        "segment_id": "segment_id",
        "activity_status": "activity_status",
        "location": "location",
        "gender": "gender",
        "customer_tenure_months": "customer_tenure_months"
    },
    "aliases": {
        "customer_type": "segment_name",
        "customer_segment": "segment_name",
        "customer_category": "segment_name",
        "profitability": "avg_revenue_per_customer",
        "revenue": "total_revenue"
    },
    "date_column": "updated_at",
    "primary_key": "customer_id"
}

dim_products_semantic = {
    "table": "dim_products",
    "description": "Product dimension table with product groups and tax information",
    "actual_columns": ["product_sku", "product_description", "product_category", "gst_rate", "product_group"],
    "metrics": {
        "product_count": "COUNT(DISTINCT product_sku)",
        "avg_gst_rate": "AVG(gst_rate)"
    },
    "dimensions": {
        "product_group": "product_group",
        "product_category": "product_category",
        "product_sku": "product_sku",
        "product_description": "product_description"
    },
    "aliases": {
        "product_type": "product_group",
        "category": "product_category",
        "product": "product_sku"
    },
    "primary_key": "product_sku"
}

# Additional semantic models can be added here
stg_bitcoin_semantic = {
    "table": "dbt_skamra_streaming.stg_bitcoin",  # Full schema qualification
    "description": "Bitcoin price streaming data with volatility analysis",
    "actual_columns": ["id", "source", "price", "change_24h", "event_timestamp", "ingestion_timestamp",
                      "volatility_category", "price_date", "price_hour", "day_of_week",
                      "previous_price", "is_valid_record", "dbt_updated_at"],
    "metrics": {
        "avg_price": "AVG(price)",
        "max_price": "MAX(price)",
        "min_price": "MIN(price)",
        "current_price": "price",
        "price_volatility": "STDDEV(change_24h)",
        "price_records": "COUNT(*)",
        "avg_change": "AVG(change_24h)",
        "max_change": "MAX(change_24h)",
        "min_change": "MIN(change_24h)"
    },
    "dimensions": {
        "volatility_category": "volatility_category",
        "price_date": "price_date",
        "price_hour": "price_hour",
        "day_of_week": "day_of_week",
        "source": "source",
        "date": "price_date",
        "hour": "price_hour"
    },
    "aliases": {
        "bitcoin_price": "avg_price",
        "btc_price": "avg_price",
        "price": "avg_price",
        "volatility": "volatility_category",
        "change": "avg_change",
        "daily_change": "change_24h",
        "date": "price_date",
        "time": "price_hour"
    },
    "date_column": "event_timestamp",
    "primary_key": "id"
}

# Registry of all available semantic models
SEMANTIC_MODELS = {
    "fct_sales": fct_sales_semantic,
    "fct_customer_segments": fct_customer_segments_semantic,
    "dim_products": dim_products_semantic,
    "stg_bitcoin": stg_bitcoin_semantic
}
