#!/usr/bin/env python3
"""
Simple test to verify Confluent Cloud connectivity and basic functionality
"""

import os
import sys
import json
import time
from confluent_kafka import Producer, Consumer
from dotenv import load_dotenv

def test_basic_connectivity():
    """Test basic Confluent Cloud connectivity"""
    
    load_dotenv()
    
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'ssl.endpoint.identification.algorithm': 'https',
    }
    
    # Check required config
    if not all([config['bootstrap.servers'], config['sasl.username'], config['sasl.password']]):
        print("❌ Missing required Confluent Cloud configuration")
        return False
    
    print("🔗 Testing basic connectivity...")
    print(f"   Bootstrap: {config['bootstrap.servers']}")
    print(f"   API Key: {config['sasl.username'][:8]}...")
    
    try:
        # Test producer connection
        producer = Producer(config)
        producer.flush(timeout=10)
        print("✅ Producer connection successful")
        
        # Test consumer connection
        consumer_config = {
            **config,
            'group.id': 'simple-test-group',
            'auto.offset.reset': 'latest'
        }
        
        consumer = Consumer(consumer_config)
        consumer.subscribe(['financial-transactions'])
        
        # Just test connection, don't wait for messages
        consumer.poll(timeout=1.0)
        consumer.close()
        print("✅ Consumer connection successful")
        
        # Test sending a message
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Simple connectivity test'
        }
        
        producer.produce(
            'financial-transactions',
            key='test',
            value=json.dumps(test_message)
        )
        producer.flush(timeout=10)
        print("✅ Message sending successful")
        
        print("\n🎉 All basic connectivity tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_connectivity()
    sys.exit(0 if success else 1)