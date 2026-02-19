#!/usr/bin/env python3
"""
Test if producer configuration works
"""

import os
import sys
from confluent_kafka import Producer
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from producer.generator import load_config

def test_producer_config():
    """Test the producer's config loading"""
    
    print("Testing producer configuration...")
    
    # Load config using producer's method
    config = load_config()
    
    print(f"Config loaded: {list(config.keys())}")
    print(f"Bootstrap servers: {config.get('bootstrap.servers')}")
    print(f"API Key: {config.get('sasl.username', 'MISSING')[:8]}...")
    print(f"API Secret: {config.get('sasl.password', 'MISSING')[:8]}...")
    
    # Remove topic from config (like the producer does)
    topic = config.pop('topic', 'financial-transactions')
    print(f"Topic: {topic}")
    
    try:
        producer = Producer(config)
        producer.flush(timeout=10)
        print("✅ Producer configuration works!")
        return True
    except Exception as e:
        print(f"❌ Producer configuration failed: {e}")
        return False

if __name__ == "__main__":
    success = test_producer_config()
    sys.exit(0 if success else 1)