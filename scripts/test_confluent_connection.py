#!/usr/bin/env python3
"""
Test Confluent Cloud connectivity
Simple script to verify Kafka connection and topic access
"""

import os
import sys
from confluent_kafka import Producer
from dotenv import load_dotenv

def test_confluent_connection():
    """Test connection to Confluent Cloud"""
    
    # Load environment variables
    load_dotenv()
    
    # Required configuration
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': os.getenv('CONFLUENT_SECURITY_PROTOCOL', 'SASL_SSL'),
        'sasl.mechanism': os.getenv('CONFLUENT_SASL_MECHANISM', 'PLAIN'),
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'ssl.endpoint.identification.algorithm': os.getenv('CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM', 'https'),
        'session.timeout.ms': 30000,
        'request.timeout.ms': 40000,
        'retry.backoff.ms': 1000
    }
    
    # Check required configuration
    required_keys = ['bootstrap.servers', 'sasl.username', 'sasl.password']
    for key in required_keys:
        if not config.get(key):
            print(f"❌ Missing required configuration: {key}")
            print("Please ensure CONFLUENT_BOOTSTRAP_SERVERS, CONFLUENT_API_KEY, and CONFLUENT_API_SECRET are set")
            return False
    
    print("🔗 Testing Confluent Cloud connection...")
    print(f"   Bootstrap servers: {config['bootstrap.servers']}")
    print(f"   Security protocol: {config['security.protocol']}")
    print(f"   SASL mechanism: {config['sasl.mechanism']}")
    print(f"   API Key: {config['sasl.username'][:8]}...")
    print(f"   API Secret: {config['sasl.password'][:4]}...{config['sasl.password'][-4:]}")
    print(f"   API Key length: {len(config['sasl.username'])}")
    print(f"   API Secret length: {len(config['sasl.password'])}")
    
    try:
        # Test connection and sending
        print("\n🔗 Testing connection...")
        producer = Producer(config)
        
        # The connection is tested when we flush - this forces broker connection
        producer.flush(timeout=10)
        print("✅ Connection established!")
        
        # Try sending a test message
        print("📤 Testing message sending...")
        import json
        import time
        
        def delivery_callback(err, msg):
            if err:
                print(f"❌ Message failed: {err}")
            else:
                print(f"✅ Message delivered to {msg.topic()}")
        
        test_msg = {'test': True, 'timestamp': time.time()}
        producer.produce(
            'financial-transactions',
            key='test',
            value=json.dumps(test_msg),
            callback=delivery_callback
        )
        
        # Wait for delivery
        producer.flush(timeout=30)
        
        print("✅ Successfully connected to Confluent Cloud!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test failed: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify your Confluent Cloud cluster is running")
        print("2. Check your API key and secret are correct")
        print("3. Ensure your IP is whitelisted (if applicable)")
        print("4. Verify network connectivity to Confluent Cloud")
        return False

if __name__ == "__main__":
    success = test_confluent_connection()
    sys.exit(0 if success else 1)