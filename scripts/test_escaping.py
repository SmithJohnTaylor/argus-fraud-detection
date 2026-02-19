#!/usr/bin/env python3
"""
Test different escaping scenarios for API secret
"""

import os
import sys
from confluent_kafka import Producer
from dotenv import load_dotenv
import urllib.parse

def test_escaping_scenarios():
    """Test API secret with and without escaping"""
    
    load_dotenv()
    
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY', '').strip()
    api_secret = os.getenv('CONFLUENT_API_SECRET', '').strip()
    
    print("=== API Secret Escaping Test ===")
    print(f"Original secret: {api_secret[:8]}...{api_secret[-8:]}")
    
    # Check what special characters are in the secret
    special_chars = []
    for char in api_secret:
        if not char.isalnum():
            special_chars.append(char)
    
    unique_special = list(set(special_chars))
    print(f"Special characters found: {unique_special}")
    
    if '/' in api_secret:
        print("✓ Found forward slash(es) in secret")
    if '\\' in api_secret:
        print("✓ Found backslash(es) in secret")
    if '+' in api_secret:
        print("✓ Found plus sign(s) in secret")
    if '=' in api_secret:
        print("✓ Found equals sign(s) in secret")
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Original (no escaping)',
            'secret': api_secret
        },
        {
            'name': 'URL encoded',
            'secret': urllib.parse.quote(api_secret, safe='')
        },
        {
            'name': 'Forward slashes escaped',
            'secret': api_secret.replace('/', '\\/')
        },
        {
            'name': 'Plus signs as spaces (URL decode)',
            'secret': api_secret.replace('+', ' ')
        }
    ]
    
    for scenario in scenarios:
        print(f"\n🧪 Testing: {scenario['name']}")
        print(f"   Secret: {scenario['secret'][:8]}...{scenario['secret'][-8:]}")
        
        config = {
            'bootstrap.servers': bootstrap_servers,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'PLAIN',
            'sasl.username': api_key,
            'sasl.password': scenario['secret'],
            'ssl.endpoint.identification.algorithm': 'https',
        }
        
        try:
            producer = Producer(config)
            metadata = producer.list_topics(timeout=10)
            print(f"   ✅ SUCCESS! This is the correct format.")
            print(f"   📋 Cluster: {metadata.cluster_id}")
            return True, scenario
            
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:100]}...")
            continue
    
    print("\n❌ All escaping scenarios failed")
    return False, None

def test_manual_input():
    """Allow manual input of credentials to test copy-paste issues"""
    
    print("\n=== Manual Credential Test ===")
    print("Please manually enter your credentials (to test for copy-paste issues)")
    
    bootstrap = input("Bootstrap servers: ").strip()
    api_key = input("API Key: ").strip()
    api_secret = input("API Secret: ").strip()
    
    config = {
        'bootstrap.servers': bootstrap,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': api_key,
        'sasl.password': api_secret,
        'ssl.endpoint.identification.algorithm': 'https',
    }
    
    try:
        producer = Producer(config)
        metadata = producer.list_topics(timeout=10)
        print(f"✅ SUCCESS with manually entered credentials!")
        print(f"📋 Cluster: {metadata.cluster_id}")
        
        # Compare with .env values
        load_dotenv()
        env_secret = os.getenv('CONFLUENT_API_SECRET', '').strip()
        
        if api_secret != env_secret:
            print(f"\n⚠️  .env secret differs from manual input!")
            print(f"   .env length: {len(env_secret)}")
            print(f"   Manual length: {len(api_secret)}")
            print(f"   .env ends with: ...{env_secret[-8:]}")
            print(f"   Manual ends with: ...{api_secret[-8:]}")
            
            # Character by character comparison
            for i, (a, b) in enumerate(zip(env_secret, api_secret)):
                if a != b:
                    print(f"   First difference at position {i}: .env='{a}' manual='{b}'")
                    break
        
        return True
        
    except Exception as e:
        print(f"❌ Failed with manual input too: {e}")
        return False

def main():
    print("🔍 Testing API Secret Escaping Scenarios\n")
    
    # Test different escaping
    success, working_scenario = test_escaping_scenarios()
    
    if success:
        print(f"\n🎉 Found working configuration: {working_scenario['name']}")
        print("Update your code to use this format.")
        return True
    
    # If all automated tests fail, try manual input
    manual_success = test_manual_input()
    
    if not manual_success:
        print("\n🚨 All tests failed. This suggests:")
        print("1. API key/secret are incorrect")
        print("2. Network/firewall issues")
        print("3. Cluster is not accessible")
        print("4. API key lacks permissions")
        
    return manual_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)