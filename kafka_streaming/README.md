# 🚀 Bitcoin & News Streaming Pipeline

Simple **real-time streaming** from Bitcoin prices and news headlines to Snowflake via Kafka.

## 📊 Data Sources

### ✅ **No API Key Required (Works Immediately)**
- **CoinGecko API**: Real-time Bitcoin prices & 24hr changes

### 🔑 **Free API Key (Optional)**
- **NewsAPI**: Live business news headlines (1,000 calls/day free)

## 🏗️ Architecture

```
Bitcoin API → Producer → Kafka Topics → Consumer → Snowflake Tables
News API         ↓           ↓            ↓              ↓
    ↓         JSON       2 Topics    Real-time      STREAMING
    ↓        Events      bitcoin     Processing     Schema
    ↓                    news                       bitcoin_prices
    ↓                                              news_headlines
    └── Real-time data every 10 seconds ──────────────┘
```

## 🚀 Quick Start

### 1. Start Kafka Cluster
```bash
docker-compose up -d
```

**Verify at:** http://localhost:8080 (Kafka UI)

### 2. Set Up Environment
```bash
# Create virtual environment
python -m venv .env
source .env/bin/activate  # Windows: .env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure APIs (Optional)

**Get Free API Keys:**
- Weather: https://openweathermap.org/api (1,000 calls/day free)
- News: https://newsapi.org (1,000 requests/day free)

**Update `producer_simple.py`:**
```python
# Line 53: Replace with your NewsAPI key
api_key = "YOUR_NEWS_API_KEY"  # Get free at newsapi.org
```

### 4. Configure Snowflake

**Update `consumer_snowflake.py`:**
```python
self.snowflake_config = {
    'user': 'your_username',
    'password': 'your_password',
    'account': 'your_account',
    'warehouse': 'COMPUTE_WH',
    'database': 'MARKETING_INSIGHTS_DB'
}
```

### 5. Run the Pipeline

#### **Option A: Test with Console First (Recommended)**

**Terminal 1 - Start Console Consumer:**
```bash
python consumer_console.py
```

**Terminal 2 - Start Producer:**
```bash
python producer_simple.py
```

Verify data format and APIs working, then move to Snowflake:

#### **Option B: Full Pipeline with Snowflake**

**Terminal 1 - Start Snowflake Consumer:**
```bash
python consumer_snowflake.py
```

**Terminal 2 - Start Producer:**
```bash
python producer_simple.py
```

## 📋 What You'll See

### Producer Logs:
```
🚀 Starting simplified data producer...
📤 Bitcoin: $67,234.50 (+2.34%)
📰 News: Reuters
```

### Consumer Logs:
```
✅ Connected to Snowflake
💰 Bitcoin data inserted: $67,234.50 (+2.34%)
📰 News data inserted: Reuters
```

### Snowflake Tables:
- `STREAMING.BITCOIN_PRICES` - Real Bitcoin prices & 24hr changes
- `STREAMING.NEWS_HEADLINES` - Live business news headlines

## 🔍 Monitoring

- **Kafka UI**: http://localhost:8080
- **Topics**: `bitcoin`, `news`
- **Latency**: < 5 seconds from API to Snowflake

## ⚡ API Rate Limits & Frequency

- **Bitcoin API (CoinGecko)**: Unlimited, fetched every 30 seconds
- **News API**: 1,000 requests/day free tier, fetched every 90 seconds
- **Daily calculation**: 90-second intervals = 960 calls/day for 16 hours (within 1000 limit)
- **💡 Tip**: Turn off at night to stay comfortably within NewsAPI limits

## 📈 Demo Queries

```sql
-- Real-time Bitcoin prices
SELECT price, change_24h, event_timestamp
FROM STREAMING.BITCOIN_PRICES
ORDER BY ingestion_timestamp DESC LIMIT 10;

-- Latest business news
SELECT headline, source_name, published_at
FROM STREAMING.NEWS_HEADLINES
ORDER BY ingestion_timestamp DESC LIMIT 5;

-- Price trend analysis
SELECT
    DATE_TRUNC('hour', event_timestamp) as hour,
    AVG(price) as avg_price,
    AVG(change_24h) as avg_change
FROM STREAMING.BITCOIN_PRICES
GROUP BY hour
ORDER BY hour DESC;
```

## 🛑 Shutdown

```bash
# Stop producer/consumer (Ctrl+C)
# Stop Kafka cluster
docker-compose down
```

## ✨ Academic Value

Demonstrates:
- ✅ **Real-time streaming** (< 5 min latency)
- ✅ **Live external APIs** (Bitcoin prices + news)
- ✅ **Kafka topics & consumers**
- ✅ **Snowflake integration**
- ✅ **Separate tables** for different data types

Perfect for academic streaming pipeline demo! 🎯
