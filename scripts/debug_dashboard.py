#!/usr/bin/env python3
"""
Debug dashboard connectivity and data flow
"""

import os
import json
import time
from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv

def debug_dashboard():
    """Debug dashboard data flow"""
    
    load_dotenv()
    
    # Simple config like we use in producer
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'group.id': 'debug-dashboard-group',
        'auto.offset.reset': 'earliest'
    }
    
    print("🔍 Debugging dashboard data flow...")
    print(f"   Bootstrap: {config['bootstrap.servers']}")
    print(f"   API Key: {config['sasl.username'][:8]}...")
    
    topics_to_check = ['financial-transactions', 'ai-decisions', 'alerts']
    
    for topic in topics_to_check:
        print(f"\n📋 Checking topic: {topic}")
        
        try:
            consumer = Consumer(config)
            consumer.subscribe([topic])
            
            message_count = 0
            timeout_count = 0
            max_messages = 10
            max_timeouts = 5
            
            print(f"   Polling for messages (max {max_messages})...")
            
            while message_count < max_messages and timeout_count < max_timeouts:
                msg = consumer.poll(timeout=2.0)
                
                if msg is None:
                    timeout_count += 1
                    print(f"   ... no message (timeout {timeout_count}/{max_timeouts})")
                    continue
                
                if msg.error():
                    print(f"   ❌ Consumer error: {msg.error()}")
                    break
                
                message_count += 1
                try:
                    value = json.loads(msg.value().decode('utf-8'))
                    print(f"   ✅ Message {message_count}: {list(value.keys()) if isinstance(value, dict) else type(value)}")
                    
                    # Show a sample of the first message
                    if message_count == 1:
                        print(f"      Sample data: {str(value)[:100]}...")
                        
                except Exception as e:
                    print(f"   ⚠️  Message {message_count}: Could not parse JSON - {e}")
                    print(f"      Raw value: {str(msg.value())[:100]}...")
            
            consumer.close()
            
            if message_count == 0:
                print(f"   📭 No messages found in {topic}")
            else:
                print(f"   📨 Found {message_count} messages in {topic}")
                
        except Exception as e:
            print(f"   ❌ Failed to read from {topic}: {e}")
    
    print(f"\n🏁 Debug complete!")

if __name__ == "__main__":
    debug_dashboard()