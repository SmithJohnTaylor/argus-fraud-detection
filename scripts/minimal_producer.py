#!/usr/bin/env python3
"""
Minimal producer test with absolute bare minimum configuration
"""

import os
import json
import time
from confluent_kafka import Producer
from dotenv import load_dotenv

def minimal_test():
    """Minimal producer test"""
    
    load_dotenv()
    
    # Absolute minimum config
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'sasl.mechanism': 'PLAIN',
        'security.protocol': 'SASL_SSL',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET')
    }
    
    print("🔗 Minimal producer test...")
    print(f"   Bootstrap: {config['bootstrap.servers']}")
    print(f"   Username: {config['sasl.username']}")
    
    try:
        producer = Producer(config)
        
        # Just try to create the producer and flush - no actual message
        print("📤 Testing producer creation...")
        producer.flush(timeout=5)
        print("✅ Producer created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        return False

if __name__ == "__main__":
    minimal_test()