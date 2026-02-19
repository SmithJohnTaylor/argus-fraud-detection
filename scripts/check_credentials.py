#!/usr/bin/env python3
"""
Check credential formatting and content
"""

import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('CONFLUENT_API_KEY')
api_secret = os.getenv('CONFLUENT_API_SECRET') 
bootstrap = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')

print("Credential check:")
print(f"API Key: {repr(api_key)}")
print(f"API Secret: {repr(api_secret[:20] + '...' if api_secret else None)}")
print(f"Bootstrap: {repr(bootstrap)}")

print("\nCredential validation:")
print(f"API Key length: {len(api_key) if api_key else 0}")
print(f"API Secret length: {len(api_secret) if api_secret else 0}")
print(f"Bootstrap servers: {bootstrap}")

# Check for common issues
if api_key:
    if api_key.startswith(' ') or api_key.endswith(' '):
        print("⚠️  API Key has leading/trailing spaces")
    if '\n' in api_key or '\r' in api_key:
        print("⚠️  API Key contains newline characters")

if api_secret:
    if api_secret.startswith(' ') or api_secret.endswith(' '):
        print("⚠️  API Secret has leading/trailing spaces")
    if '\n' in api_secret or '\r' in api_secret:
        print("⚠️  API Secret contains newline characters")