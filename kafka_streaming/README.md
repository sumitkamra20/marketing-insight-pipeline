# 🚀 Bitcoin & News Streaming Pipeline

**Enhanced** real-time streaming from Bitcoin prices and **enriched news data** to Snowflake via Kafka.

## 📊 Data Sources

### ✅ **No API Key Required (Works Immediately)**
- **CoinGecko API**: Real-time Bitcoin prices & 24hr changes

### 🔑 **Enhanced News Data (Free API Key)**
- **NewsAPI**: Rich business news with descriptions, categories, sentiment analysis
- **Multiple Sources**: BBC News, CNN, Reuters for variety
- **Analytical Fields**: Word count, URLs, crypto mentions, categorization

## 🏗️ Architecture

```
Bitcoin API → Enhanced Producer → Kafka Topics → Consumer → Snowflake Tables
News APIs        ↓                   ↓            ↓              ↓
(BBC/CNN/        ↓               2 Topics    Real-time      STREAMING
Reuters)         ↓               bitcoin     Processing     Schema
    ↓            ↓               news                       bitcoin_prices
    ↓            ↓                                         news_enriched
    └── Enhanced data every 30-60 seconds ──────────────────┘
```

## 🚀 Quick Start

### 1. Start Kafka Cluster
```bash
docker-compose up -d
```

**Verify at:** http://localhost:8080 (Kafka UI)

### 2. Set Up Environment
```bash
# Install dependencies
pip install -r requirements.txt
```

### 3. Configure APIs

**Your NewsAPI key is already configured!** ✅
- API Key: `e604699632584dbcb054c47c9577b067`
- Multiple sources: BBC News, CNN, Reuters

### 4. Run the Enhanced Pipeline

#### **Option A: Test with Console First (Recommended)**

**Terminal 1 - Start Console Consumer:**
```bash
python consumer_console.py
```

**Terminal 2 - Start Enhanced Producer:**
```bash
python producer_enhanced.py
```

Verify rich data format, then move to Snowflake:

#### **Option B: Full Pipeline with Snowflake**

**Terminal 1 - Start Snowflake Consumer:**
```bash
python consumer_snowflake.py
```

**Terminal 2 - Start Enhanced Producer:**
```bash
python producer_enhanced.py
```

## 📋 Enhanced Data Structure

### **Bitcoin Data (Every 30 seconds):**
```json
{
  "source": "bitcoin",
  "price": 104272.00,
  "change_24h": -1.03,
  "timestamp": "2025-01-15T10:30:45"
}
```

### **Enhanced News Data (Every 60 seconds):**
```json
{
  "source": "news",
  "headline": "Fed Signals Rate Cuts Amid Inflation Concerns",
  "description": "Federal Reserve officials indicated potential interest rate reductions...",
  "category": "economy",
  "source_name": "Reuters",
  "url": "https://...",
  "published_at": "2025-01-15T10:30:00Z",
  "word_count": 156,
  "has_crypto_mention": false,
  "timestamp": "2025-01-15T10:30:45"
}
```

## 🔍 Monitoring

- **Kafka UI**: http://localhost:8080
- **Topics**: `bitcoin`, `news`
- **Latency**: < 5 seconds from API to Snowflake

## ⚡ Demo-Optimized Frequency

- **Bitcoin API**: Every 30 seconds (unlimited)
- **Enhanced News API**: Every 60 seconds (perfect for 1-hour demo)
- **Demo Usage**: ~60 news calls/hour (well within limits)
- **Rich Analytics**: Categories, sentiment keywords, word counts

## 📈 Enhanced Demo Queries

```sql
-- Real-time Bitcoin prices with trends
SELECT price, change_24h, event_timestamp
FROM STREAMING.BITCOIN_PRICES
ORDER BY ingestion_timestamp DESC LIMIT 10;

-- Rich news analytics
SELECT
    headline,
    category,
    source_name,
    word_count,
    has_crypto_mention,
    published_at
FROM STREAMING.NEWS_ENRICHED
ORDER BY ingestion_timestamp DESC LIMIT 5;

-- News categorization analysis
SELECT
    category,
    COUNT(*) as article_count,
    AVG(word_count) as avg_word_count
FROM STREAMING.NEWS_ENRICHED
GROUP BY category
ORDER BY article_count DESC;
```

## 🛑 Shutdown

```bash
# Stop producer/consumer (Ctrl+C)
# Stop Kafka cluster
docker-compose down
```

## ✨ Enhanced Academic Value

Demonstrates:
- ✅ **Real-time streaming** (< 5 min latency)
- ✅ **Multiple live APIs** (Bitcoin + Multi-source news)
- ✅ **Rich data structures** (analytical fields, categorization)
- ✅ **Kafka topics & consumers**
- ✅ **Snowflake integration**
- ✅ **Demo-optimized timing** (60-second news for 1-hour presentation)
- ✅ **Analytical potential** (sentiment, categories, word counts)

Perfect for academic streaming pipeline demonstration! 🎯
