#!/usr/bin/env python3
"""
Verify Confluent Cloud credentials format and test different configurations
"""

import os
import sys
from confluent_kafka import Producer
from dotenv import load_dotenv

def test_credentials():
    """Test various credential configurations"""
    
    load_dotenv()
    
    # Get raw credentials
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY')
    api_secret = os.getenv('CONFLUENT_API_SECRET')
    
    print("=== Raw Credential Analysis ===")
    print(f"Bootstrap: {bootstrap_servers}")
    print(f"API Key: '{api_key}'")
    print(f"API Secret: '{api_secret[:8]}...{api_secret[-8:]}'")
    print(f"Key length: {len(api_key)}")
    print(f"Secret length: {len(api_secret)}")
    
    # Check for whitespace or hidden characters
    if api_key != api_key.strip():
        print("⚠️  API Key has leading/trailing whitespace!")
        api_key = api_key.strip()
        
    if api_secret != api_secret.strip():
        print("⚠️  API Secret has leading/trailing whitespace!")
        api_secret = api_secret.strip()
    
    # Test minimal configuration (most compatible)
    print("\n=== Testing Minimal Configuration ===")
    config = {
        'bootstrap.servers': bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': api_key,
        'sasl.password': api_secret,
    }
    
    try:
        print("Creating producer...")
        producer = Producer(config)
        
        print("Attempting to list topics (this will trigger auth)...")
        metadata = producer.list_topics(timeout=15)
        
        print(f"✅ SUCCESS! Connected to cluster: {metadata.cluster_id}")
        print(f"📋 Available topics: {list(metadata.topics.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_with_confluent_cli_format():
    """Test using the exact format that confluent CLI would use"""
    
    load_dotenv()
    
    print("\n=== Testing Confluent CLI Compatible Format ===")
    
    # This mimics how confluent CLI constructs the config
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY', '').strip()
    api_secret = os.getenv('CONFLUENT_API_SECRET', '').strip()
    
    # Alternative property names that some versions use
    config = {
        'bootstrap.servers': bootstrap_servers,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',  # Note: plural - some versions need this
        'sasl.username': api_key,
        'sasl.password': api_secret,
        'client.id': 'python-test-client'
    }
    
    try:
        producer = Producer(config)
        metadata = producer.list_topics(timeout=15)
        print(f"✅ SUCCESS with plural 'sasl.mechanisms'!")
        return True
    except Exception as e:
        print(f"❌ Failed with plural form: {e}")
        
    # Try without client.id
    config.pop('client.id')
    config['sasl.mechanism'] = config.pop('sasl.mechanisms')  # Change to singular
    
    try:
        producer = Producer(config)
        metadata = producer.list_topics(timeout=15)
        print(f"✅ SUCCESS with singular 'sasl.mechanism'!")
        return True
    except Exception as e:
        print(f"❌ Failed with singular form: {e}")
        
    return False

def main():
    print("🔍 Confluent Cloud Credential Verification\n")
    
    # Test 1: Basic format check
    success1 = test_credentials()
    
    # Test 2: CLI compatible format
    success2 = test_with_confluent_cli_format()
    
    if not (success1 or success2):
        print("\n🚨 Both tests failed. Potential issues:")
        print("1. API Key/Secret are incorrect")
        print("2. Cluster is not accessible from your network")
        print("3. API Key doesn't have sufficient permissions")
        print("4. Try generating a new API key/secret pair")
        print("\n💡 Next steps:")
        print("1. Verify in Confluent Cloud UI that the cluster is running")
        print("2. Check that your API key has 'CloudClusterAdmin' permissions")
        print("3. Try creating a new API key/secret pair")
        print("4. Test with confluent CLI: `confluent kafka topic list`")
        
        return False
    
    print("\n✅ Authentication successful!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)