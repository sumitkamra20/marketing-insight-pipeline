#!/usr/bin/env python3
"""
Simple console consumer for testing Kafka producer output
Prints messages to console for debugging and validation
"""

import json
import logging
from datetime import datetime
from confluent_kafka import Consumer, KafkaError
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsoleKafkaConsumer:
    def __init__(self):
        # Kafka configuration
        self.consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': 'console-test-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'session.timeout.ms': 6000,
            'heartbeat.interval.ms': 1000
        })

        # Topics to subscribe to
        self.topics = ['bitcoin', 'news']

        # Message counters
        self.message_counts = {'bitcoin': 0, 'news': 0, 'total': 0}

    def format_bitcoin_message(self, data: Dict[str, Any]) -> str:
        """Format Bitcoin message for console display"""
        price = data.get('price', 0)
        change = data.get('change_24h', 0)
        timestamp = data.get('timestamp', 'N/A')

        return f"💰 Bitcoin: ${price:,.2f} ({change:+.2f}%) at {timestamp}"

    def format_news_message(self, data: Dict[str, Any]) -> str:
        """Format Enhanced News message for console display"""
        headline = data.get('headline', 'N/A')[:60] + "..." if len(data.get('headline', '')) > 60 else data.get('headline', 'N/A')
        source = data.get('source_name', 'Unknown')
        category = data.get('category', 'general')
        word_count = data.get('word_count', 0)
        description = data.get('description', 'No description')[:100] + "..." if len(data.get('description', '')) > 100 else data.get('description', 'No description')
        has_crypto = data.get('has_crypto_mention', False)
        timestamp = data.get('timestamp', 'N/A')

        # Enhanced display with analytical fields
        crypto_flag = "🪙" if has_crypto else "📰"
        return f"{crypto_flag} News: [{category.upper()}] {source} | {headline}\n    📝 {description}\n    📊 {word_count} words | {timestamp}"

    def process_message(self, message):
        """Process and display a single Kafka message"""
        try:
            # Parse JSON data
            data = json.loads(message.value().decode('utf-8'))
            topic = message.topic()

            # Update counters
            self.message_counts[topic] = self.message_counts.get(topic, 0) + 1
            self.message_counts['total'] += 1

            # Format and display message based on topic
            if topic == 'bitcoin':
                formatted_msg = self.format_bitcoin_message(data)
                print(f"[{self.message_counts['bitcoin']:3d}] {formatted_msg}")
            elif topic == 'news':
                formatted_msg = self.format_news_message(data)
                print(f"[{self.message_counts['news']:3d}] {formatted_msg}")

                # Show enhanced fields summary for news
                if data.get('description') and len(data.get('description', '')) > 10:
                    print(f"    🔗 URL: {data.get('url', 'N/A')}")
                    print(f"    📅 Published: {data.get('published_at', 'N/A')}")
                    print(f"    ✨ Enhanced data fields: ✅")
                else:
                    print(f"    ⚠️  Basic data only - enhanced fields missing")
            else:
                print(f"❓ Unknown topic '{topic}': {data}")

            # Show raw JSON for debugging (optional)
            if logger.isEnabledFor(logging.DEBUG):
                print(f"    Raw JSON: {json.dumps(data, indent=2)}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
            print(f"❌ Invalid JSON: {message.value().decode('utf-8')}")
        except Exception as e:
            logger.error(f"❌ Message processing error: {e}")

    def print_stats(self):
        """Print consumption statistics"""
        print(f"\n📊 Messages consumed - Bitcoin: {self.message_counts.get('bitcoin', 0)}, "
              f"News: {self.message_counts.get('news', 0)}, "
              f"Total: {self.message_counts['total']}")

    def run(self):
        """Main consumer loop"""
        print("🚀 Starting Console Kafka Consumer...")
        print("📋 This will display all messages from producer for testing")
        print(f"📊 Monitoring topics: {', '.join(self.topics)}")
        print("🔍 Kafka UI: http://localhost:8080")
        print("⏹️  Press Ctrl+C to stop\n")

        try:
            # Subscribe to topics
            self.consumer.subscribe(self.topics)

            stats_counter = 0

            while True:
                # Poll for messages
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    # Show stats every 30 seconds when no messages
                    stats_counter += 1
                    if stats_counter >= 30:
                        self.print_stats()
                        stats_counter = 0
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"📍 End of partition {msg.topic()}/{msg.partition()}")
                    else:
                        logger.error(f"❌ Consumer error: {msg.error()}")
                    continue

                # Process the message
                self.process_message(msg)

                # Reset stats counter when actively receiving messages
                stats_counter = 0

        except KeyboardInterrupt:
            print("\n🛑 Shutting down console consumer...")
            self.print_stats()
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
        finally:
            self.consumer.close()
            print("✅ Console consumer stopped")

if __name__ == '__main__':
    consumer = ConsoleKafkaConsumer()
    consumer.run()
