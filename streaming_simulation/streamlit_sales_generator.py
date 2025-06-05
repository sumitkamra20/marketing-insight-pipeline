import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import snowflake.connector
import time
import json

# Streamlit App Configuration
st.set_page_config(page_title="Sales Transaction Simulator", layout="wide")
st.title("🛒 Real-time Sales Transaction Simulator")
st.markdown("**Simulating Kafka-like streaming data ingestion**")

# Sample data for realistic transactions
CUSTOMERS = list(range(17000, 18000))  # Sample customer IDs
PRODUCTS = [
    {'sku': 'GGOENEBJ079499', 'desc': 'Nest Learning Thermostat', 'category': 'Nest-USA', 'price': 249.99},
    {'sku': 'GGOEGFKQ020399', 'desc': 'Google Laptop Stickers', 'category': 'Office', 'price': 15.99},
    {'sku': 'GGOEGAAB010516', 'desc': 'Google Apparel Hoodie', 'category': 'Apparel', 'price': 65.00},
    {'sku': 'GGOEGBJL013999', 'desc': 'Google Backpack', 'category': 'Bags', 'price': 45.99},
    {'sku': 'GGOEGHPB071610', 'desc': 'Google Water Bottle', 'category': 'Drinkware', 'price': 22.50}
]

def generate_transaction():
    """Generate a realistic sales transaction"""
    customer_id = random.choice(CUSTOMERS)
    product = random.choice(PRODUCTS)
    quantity = random.randint(1, 5)

    # Add some price variation
    price_variation = random.uniform(0.9, 1.1)
    avg_price = round(product['price'] * price_variation, 2)

    delivery_charges = random.choice([0, 5.99, 8.99, 12.99])
    coupon_status = random.choice(['Used', 'Not_Used', 'Not_Used', 'Not_Used'])  # 25% coupon usage

    return {
        'customerid': customer_id,
        'transaction_id': random.randint(30000, 99999),
        'transaction_date': datetime.now().strftime('%m/%d/%Y'),
        'product_sku': product['sku'],
        'product_description': product['desc'],
        'product_category': product['category'],
        'quantity': quantity,
        'avg_price': avg_price,
        'delivery_charges': delivery_charges,
        'coupon_status': coupon_status
    }

# Streamlit Interface
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎮 Transaction Generator Controls")

    # Configuration
    transactions_per_batch = st.slider("Transactions per batch", 1, 10, 3)
    delay_seconds = st.slider("Delay between batches (seconds)", 1, 10, 2)

    # Start/Stop buttons
    if 'generating' not in st.session_state:
        st.session_state.generating = False

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Start Generating", disabled=st.session_state.generating):
            st.session_state.generating = True

    with col_btn2:
        if st.button("⏹️ Stop", disabled=not st.session_state.generating):
            st.session_state.generating = False

with col2:
    st.subheader("📊 Statistics")

    # Initialize counters
    if 'total_transactions' not in st.session_state:
        st.session_state.total_transactions = 0
    if 'total_revenue' not in st.session_state:
        st.session_state.total_revenue = 0.0

    st.metric("Total Transactions", st.session_state.total_transactions)
    st.metric("Total Revenue", f"${st.session_state.total_revenue:,.2f}")

# Transaction Display Area
st.subheader("📋 Live Transaction Feed")
transaction_placeholder = st.empty()

# Transaction Generation Logic
if st.session_state.generating:
    with st.spinner('Generating transactions...'):
        transactions = []

        for i in range(transactions_per_batch):
            transaction = generate_transaction()
            transactions.append(transaction)

            # Update statistics
            st.session_state.total_transactions += 1
            st.session_state.total_revenue += transaction['quantity'] * transaction['avg_price']

        # Display transactions
        df = pd.DataFrame(transactions)
        transaction_placeholder.dataframe(df, use_container_width=True)

        # Simulate data insertion to Snowflake (you'll implement this)
        st.success(f"✅ Generated {len(transactions)} transactions")

        # Wait before next batch
        time.sleep(delay_seconds)

        # Auto-refresh
        st.rerun()

# Instructions
st.markdown("---")
st.markdown("""
### 🎯 **Demo Instructions:**

1. **Start the simulator** to generate streaming transactions
2. **Each transaction** represents a Kafka message
3. **Data flows**: Streamlit → Snowflake → dbt staging → dbt incremental fact table
4. **Demonstrates**: Real-time data ingestion + incremental processing

### 🔧 **Next Steps:**
- Implement Snowflake connection
- Add data insertion logic
- Set up dbt incremental refresh trigger
""")
