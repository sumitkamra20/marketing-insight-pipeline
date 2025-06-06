#!/usr/bin/env python3
"""
Real-time data producer for marketing insights
Streams data from multiple APIs to Kafka
"""

import json
import time
import requests
from datetime import datetime
from confluent_kafka import Producer
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealDataProducer:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': 'localhost:9092',
            'client.id': 'real-data-producer'
        })

        # API configurations (add your keys)
        self.apis = {
            'crypto': {
                'url': 'https://api.coingecko.com/api/v3/simple/price',
                'params': 'ids=bitcoin&vs_currencies=usd&include_24hr_change=true'
            },
            'news': {
                'url': 'https://newsapi.org/v2/top-headlines',
                'key': 'YOUR_NEWS_KEY',  # Free at newsapi.org
                'category': 'business'
            }
        }

    def delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.info(f'Message delivered to {msg.topic()} [{msg.partition()}]')



    def get_crypto_data(self) -> Dict[str, Any]:
        """Fetch real cryptocurrency data (no API key needed)"""
        try:
            url = f"{self.apis['crypto']['url']}?{self.apis['crypto']['params']}"
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
            logger.error(f"Crypto API error: {e}")
        return None

    def get_news_data(self) -> Dict[str, Any]:
        """Fetch real news headlines"""
        try:
            url = f"{self.apis['news']['url']}?category={self.apis['news']['category']}&apiKey={self.apis['news']['key']}&pageSize=1"
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
        """Main producer loop"""
        logger.info("🚀 Starting real-time data producer...")
        logger.info("📊 Available at Kafka UI: http://localhost:8080")

        data_sources = [
            self.get_crypto_data,      # Always works (no API key)
            self.get_news_data,        # Needs API key
        ]

        try:
            while True:
                for source_func in data_sources:
                    try:
                        # Get data from source
                        data = source_func()

                        if data:
                            # Determine topic based on source
                            topic = data['source']  # Simple topic names: 'bitcoin', 'news'

                            # Produce to Kafka
                            self.producer.produce(
                                topic=topic,
                                key=data['source'],
                                value=json.dumps(data),
                                callback=self.delivery_callback
                            )

                            logger.info(f"📤 Sent {data['source']} data to topic '{topic}'")

                        # Wait between API calls
                        time.sleep(2)

                    except Exception as e:
                        logger.error(f"Error with {source_func.__name__}: {e}")

                # Poll for delivery callbacks
                self.producer.poll(0)

                # Wait before next cycle
                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down producer...")
        finally:
            self.producer.flush()

if __name__ == '__main__':
    producer = RealDataProducer()
    producer.run()
