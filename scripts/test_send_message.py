#!/usr/bin/env python3
"""
Test if we can actually send a message to Confluent Cloud
"""

import os
import sys
import json
import time
from confluent_kafka import Producer
from dotenv import load_dotenv

def test_send_message():
    """Test sending a message to Confluent Cloud"""
    
    load_dotenv()
    
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'ssl.endpoint.identification.algorithm': 'https',
    }
    
    print("🔗 Testing message sending...")
    print(f"   Bootstrap: {config['bootstrap.servers']}")
    print(f"   API Key: {config['sasl.username'][:8]}...")
    
    sent_count = 0
    error_count = 0
    
    def delivery_callback(err, msg):
        nonlocal sent_count, error_count
        if err:
            print(f"❌ Message delivery failed: {err}")
            error_count += 1
        else:
            print(f"✅ Message delivered to {msg.topic()}[{msg.partition()}] at offset {msg.offset()}")
            sent_count += 1
    
    try:
        producer = Producer(config)
        
        # Send a test message
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Test message from producer'
        }
        
        print("📤 Sending test message...")
        producer.produce(
            'financial-transactions',
            key='test-key',
            value=json.dumps(test_message),
            callback=delivery_callback
        )
        
        print("⏳ Waiting for delivery confirmation...")
        # Poll for delivery reports with longer timeout
        start_time = time.time()
        while time.time() - start_time < 30:  # Wait up to 30 seconds
            producer.poll(0.1)
            if sent_count > 0 or error_count > 0:
                break
        
        # Final flush
        remaining = producer.flush(10)
        
        print(f"\n📊 Results:")
        print(f"   Messages sent: {sent_count}")
        print(f"   Messages failed: {error_count}")
        print(f"   Messages remaining in queue: {remaining}")
        
        return sent_count > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_send_message()
    print(f"\n{'✅ Success!' if success else '❌ Failed!'}")
    sys.exit(0 if success else 1)