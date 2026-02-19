#!/usr/bin/env python3
"""
Debug Confluent Cloud authentication
Minimal test to isolate authentication issues
"""

import os
import sys
from confluent_kafka import Producer
from dotenv import load_dotenv

def test_minimal_connection():
    """Minimal connection test with different configurations"""
    
    load_dotenv()
    
    # Get credentials
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY')
    api_secret = os.getenv('CONFLUENT_API_SECRET')
    
    print("=== Confluent Cloud Debug Information ===")
    print(f"Bootstrap servers: {bootstrap_servers}")
    print(f"API Key: {api_key}")
    print(f"API Secret: {api_secret}")
    print()
    
    if not all([bootstrap_servers, api_key, api_secret]):
        print("❌ Missing required environment variables")
        return False
    
    # Test different configurations
    configs_to_test = [
        {
            'name': 'Standard Configuration',
            'config': {
                'bootstrap.servers': bootstrap_servers,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': api_key,
                'sasl.password': api_secret,
                'ssl.endpoint.identification.algorithm': 'https',
                'ssl.endpoint.identification.algorithm': 'https',
            }
        },
        {
            'name': 'With Additional Settings',
            'config': {
                'bootstrap.servers': bootstrap_servers,
                'security.protocol': 'SASL_SSL', 
                'sasl.mechanism': 'PLAIN',
                'sasl.username': api_key,
                'sasl.password': api_secret,
                'ssl.endpoint.identification.algorithm': 'https',
                'session.timeout.ms': 30000,
                'request.timeout.ms': 40000,
                'api.version.request': True,
            }
        },
        {
            'name': 'Minimal Configuration',
            'config': {
                'bootstrap.servers': bootstrap_servers,
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',  # Note: singular form
                'sasl.username': api_key,
                'sasl.password': api_secret,
                'ssl.endpoint.identification.algorithm': 'https',
            }
        }
    ]
    
    for test_config in configs_to_test:
        print(f"🧪 Testing: {test_config['name']}")
        try:
            producer = Producer(test_config['config'])
            
            # Try to get metadata (this triggers authentication)
            metadata = producer.list_topics(timeout=10)
            print(f"   ✅ Success! Found {len(metadata.topics)} topics")
            
            # If we get here, authentication worked
            print(f"   📋 Cluster: {metadata.cluster_id}")
            if 'financial-transactions' in metadata.topics:
                print("   📝 Found financial-transactions topic")
            else:
                print("   ⚠️  financial-transactions topic not found")
            
            producer.flush()
            return True
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)}")
            if "authentication" in str(e).lower():
                print("   🔍 This appears to be an authentication error")
            continue
    
    print("\n🔍 All configurations failed. Additional troubleshooting:")
    print("1. Verify your .env file has the correct values")
    print("2. Check if API key/secret have any special characters that need escaping")
    print("3. Verify the cluster is in the expected region")
    print("4. Try running: confluent kafka topic list --cluster <cluster-id>")
    
    return False

if __name__ == "__main__":
    success = test_minimal_connection()
    sys.exit(0 if success else 1)