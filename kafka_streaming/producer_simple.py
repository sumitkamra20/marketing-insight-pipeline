#!/usr/bin/env python3
"""
Simplified real-time data producer for Bitcoin and News
Streams data from APIs to Kafka
"""

import json
import time
import requests
import os
from datetime import datetime
from confluent_kafka import Producer
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDataProducer:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': 'localhost:9092',
            'client.id': 'simple-data-producer'
        })

    def delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')

    def get_bitcoin_data(self) -> Dict[str, Any]:
        """Fetch real Bitcoin data (no API key needed)"""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return {
                    'source': 'bitcoin',
                    'price': data.get('bitcoin', {}).get('usd'),
                    'change_24h': data.get('bitcoin', {}).get('usd_24h_change'),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Bitcoin API error: {e}")
        return None

    def get_news_data(self) -> Dict[str, Any]:
        """Fetch real news headlines (requires API key)"""
        try:
            # Get API key from environment variable
            api_key = os.getenv('NEWS_API_KEY')

            if not api_key:
                logger.warning("⚠️ NEWS_API_KEY not found in .env file, skipping news data")
                return None

            url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={api_key}&pageSize=1"

            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                if articles:
                    article = articles[0]
                    return {
                        'source': 'news',
                        'headline': article.get('title'),
                        'source_name': article.get('source', {}).get('name'),
                        'published_at': article.get('publishedAt'),
                        'timestamp': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"News API error: {e}")
        return None

    def run(self):
        """Main producer loop with different frequencies for Bitcoin vs News"""
        logger.info("🚀 Starting simplified data producer...")
        logger.info("📊 Monitor at Kafka UI: http://localhost:8080")
        logger.info("💰 Bitcoin data: every 30 seconds")
        logger.info("📰 News data: every 90 seconds (to stay within 1000/day API limit)")
        logger.info("💡 Running 16 hours/day = ~960 news calls (within 1000 limit)")

        last_news_fetch = 0

        try:
            while True:
                current_time = time.time()

                # Get Bitcoin data (every 30 seconds - unlimited API)
                bitcoin_data = self.get_bitcoin_data()
                if bitcoin_data:
                    self.producer.produce(
                        topic='bitcoin',
                        key='bitcoin',
                        value=json.dumps(bitcoin_data),
                        callback=self.delivery_callback
                    )
                    logger.info(f"📤 Bitcoin: ${bitcoin_data['price']:.2f} ({bitcoin_data['change_24h']:+.2f}%)")

                # Get News data (every 90 seconds to stay within API limits)
                if current_time - last_news_fetch >= 90:  # 90 seconds = 960 calls/day for 16 hours
                    news_data = self.get_news_data()
                    if news_data:
                        self.producer.produce(
                            topic='news',
                            key='news',
                            value=json.dumps(news_data),
                            callback=self.delivery_callback
                        )
                        logger.info(f"📰 News: {news_data['source_name']}")
                    last_news_fetch = current_time

                # Poll for delivery callbacks
                self.producer.poll(0)

                # Wait before next cycle
                time.sleep(30)  # 30 seconds between Bitcoin fetches

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down producer...")
        finally:
            self.producer.flush()

if __name__ == '__main__':
    producer = SimpleDataProducer()
    producer.run()
