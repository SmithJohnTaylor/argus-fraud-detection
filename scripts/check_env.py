#!/usr/bin/env python3
"""
Check environment variable loading
"""

import os
from dotenv import load_dotenv

def check_environment():
    print("=== Environment Variable Check ===")
    
    # Check without dotenv
    print("1. Direct environment variables:")
    print(f"   CONFLUENT_BOOTSTRAP_SERVERS: {os.environ.get('CONFLUENT_BOOTSTRAP_SERVERS', 'NOT SET')}")
    print(f"   CONFLUENT_API_KEY: {os.environ.get('CONFLUENT_API_KEY', 'NOT SET')}")
    print(f"   CONFLUENT_API_SECRET: {os.environ.get('CONFLUENT_API_SECRET', 'NOT SET')}")
    
    # Load .env file
    print("\n2. Loading .env file...")
    load_dotenv()
    
    print("   After loading .env:")
    bootstrap = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY')
    api_secret = os.getenv('CONFLUENT_API_SECRET')
    
    print(f"   CONFLUENT_BOOTSTRAP_SERVERS: {bootstrap}")
    print(f"   CONFLUENT_API_KEY: {api_key}")
    print(f"   CONFLUENT_API_SECRET: {api_secret[:4] + '...' if api_secret else 'NOT SET'}")
    
    # Check for common issues
    print("\n3. Validation checks:")
    if not bootstrap:
        print("   ❌ CONFLUENT_BOOTSTRAP_SERVERS is missing")
    elif not bootstrap.endswith(':9092'):
        print("   ⚠️  Bootstrap servers should end with :9092")
    else:
        print("   ✅ Bootstrap servers look correct")
    
    if not api_key:
        print("   ❌ CONFLUENT_API_KEY is missing")
    elif len(api_key) < 10:
        print("   ⚠️  API key seems too short")
    else:
        print("   ✅ API key looks correct")
    
    if not api_secret:
        print("   ❌ CONFLUENT_API_SECRET is missing")
    elif len(api_secret) < 20:
        print("   ⚠️  API secret seems too short")
    else:
        print("   ✅ API secret looks correct")
    
    # Check for special characters that might cause issues
    if api_secret:
        special_chars = ['@', '#', '$', '%', '&', '*', '!', '+', '=']
        found_special = [char for char in special_chars if char in api_secret]
        if found_special:
            print(f"   ⚠️  API secret contains special characters: {found_special}")
            print("      These might need to be URL-encoded or escaped")

if __name__ == "__main__":
    check_environment()