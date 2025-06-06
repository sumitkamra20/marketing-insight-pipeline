#!/usr/bin/env python3
"""
Real-time consumer that streams from Kafka to Snowflake
Handles multiple topics and data sources
"""

import json
import logging
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
import snowflake.connector
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SnowflakeKafkaConsumer:
    def __init__(self):
        # Kafka configuration
        self.consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'snowflake-sink-group',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True,
            'session.timeout.ms': 6000,
            'heartbeat.interval.ms': 1000
        })

        # Snowflake configuration using your existing setup
        self.snowflake_config = {
            'user': os.getenv('SNOWFLAKE_USER', 'kafka_streaming'),  # or 'dbt_marketing'
            'password': os.getenv('SNOWFLAKE_PASSWORD', 'kafkaPassword123'),  # or 'dbtPassword123'
            'account': os.getenv('SNOWFLAKE_ACCOUNT', 'BRVIXQZ-AQ58231'),  # Correct format from account details
            'warehouse': 'MARKETING_WH',  # Using your existing warehouse
            'database': 'MARKETING_INSIGHTS_DB',  # Using your existing database
            'schema': 'STREAMING',
            'role': 'TRANSFORM'  # Using your existing role
        }

                # Topics to subscribe to
        self.topics = [
            'bitcoin',
            'news'
        ]

        self.snowflake_conn = None

    def connect_snowflake(self):
        """Establish Snowflake connection"""
        try:
            self.snowflake_conn = snowflake.connector.connect(**self.snowflake_config)
            logger.info("✅ Connected to Snowflake")

            # Create schema if not exists
            cursor = self.snowflake_conn.cursor()
            cursor.execute("CREATE SCHEMA IF NOT EXISTS STREAMING")
            cursor.close()

        except Exception as e:
            logger.error(f"❌ Snowflake connection failed: {e}")
            raise

    def create_tables(self):
        """Create Snowflake tables for different data sources"""
        cursor = self.snowflake_conn.cursor()

        tables = {
            'bitcoin_prices_raw': """
                CREATE TABLE IF NOT EXISTS bitcoin_prices_raw (
                    id STRING DEFAULT UUID_STRING(),
                    source STRING,
                    price FLOAT,
                    change_24h FLOAT,
                    event_timestamp TIMESTAMP_NTZ,
                    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    PRIMARY KEY (id)
                )
            """,
            'news_events_raw': """
                CREATE TABLE IF NOT EXISTS news_events_raw (
                    id STRING DEFAULT UUID_STRING(),
                    source STRING,
                    headline STRING,
                    description STRING,
                    category STRING,
                    source_name STRING,
                    url STRING,
                    published_at TIMESTAMP_NTZ,
                    word_count INTEGER,
                    has_crypto_mention BOOLEAN,
                    event_timestamp TIMESTAMP_NTZ,
                    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
                    PRIMARY KEY (id)
                )
            """
        }

        for table_name, ddl in tables.items():
            try:
                cursor.execute(ddl)
                logger.info(f"✅ Table {table_name} ready")
            except Exception as e:
                logger.error(f"❌ Error creating table {table_name}: {e}")

        cursor.close()

    def insert_bitcoin_data(self, data: Dict[str, Any]):
        """Insert Bitcoin data to Snowflake"""
        cursor = self.snowflake_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO bitcoin_prices_raw
                (source, price, change_24h, event_timestamp)
                VALUES (%(source)s, %(price)s, %(change_24h)s, %(timestamp)s)
            """, data)
            logger.info(f"💰 Bitcoin data inserted: ${data.get('price', 0):.2f} ({data.get('change_24h', 0):+.2f}%)")
        except Exception as e:
            logger.error(f"❌ Bitcoin insert error: {e}")
        finally:
            cursor.close()

    def insert_news_data(self, data: Dict[str, Any]):
        """Insert enhanced news data to Snowflake"""
        cursor = self.snowflake_conn.cursor()
        try:
            # Convert published_at to timestamp if needed
            if 'published_at' in data and data['published_at']:
                try:
                    # Handle ISO format timestamp
                    data['published_at'] = data['published_at'].replace('T', ' ').replace('Z', '')
                except:
                    data['published_at'] = None

            cursor.execute("""
                INSERT INTO news_events_raw
                (source, headline, description, category, source_name, url,
                 published_at, word_count, has_crypto_mention, event_timestamp)
                VALUES (%(source)s, %(headline)s, %(description)s, %(category)s,
                        %(source_name)s, %(url)s, %(published_at)s, %(word_count)s,
                        %(has_crypto_mention)s, %(timestamp)s)
            """, data)
            logger.info(f"📰 Enhanced news inserted: [{data.get('category', 'general')}] {data.get('source_name', 'Unknown')}")
        except Exception as e:
            logger.error(f"❌ News insert error: {e}")
        finally:
            cursor.close()

    def process_message(self, message):
        """Process a single Kafka message"""
        try:
            # Parse JSON data
            data = json.loads(message.value().decode('utf-8'))
            topic = message.topic()

            # Route to appropriate handler based on topic
            if topic == 'bitcoin':
                self.insert_bitcoin_data(data)
            elif topic == 'news':
                self.insert_news_data(data)
            else:
                logger.warning(f"⚠️ Unknown topic: {topic}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")

    def run(self):
        """Main consumer loop"""
        logger.info("🚀 Starting Snowflake Kafka Consumer...")

        try:
            # Connect to Snowflake
            self.connect_snowflake()
            self.create_tables()

            # Subscribe to topics
            self.consumer.subscribe(self.topics)
            logger.info(f"📋 Subscribed to topics: {', '.join(self.topics)}")
            logger.info("📊 Monitor at Kafka UI: http://localhost:8080")
            logger.info("❄️ Data flowing to Snowflake STREAMING schema")

            while True:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.topic()}/{msg.partition()}")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                # Process the message
                self.process_message(msg)

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down consumer...")
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            # Clean shutdown
            self.consumer.close()
            if self.snowflake_conn:
                self.snowflake_conn.close()
            logger.info("✅ Consumer stopped")

if __name__ == '__main__':
    consumer = SnowflakeKafkaConsumer()
    consumer.run()
