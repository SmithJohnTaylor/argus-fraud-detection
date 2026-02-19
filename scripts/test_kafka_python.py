#!/usr/bin/env python3
"""
Test Confluent Cloud connectivity using kafka-python instead of librdkafka
"""

import os
import json
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from dotenv import load_dotenv

def test_kafka_python():
    """Test Confluent Cloud with kafka-python"""
    
    load_dotenv()
    
    bootstrap_servers = os.getenv('CONFLUENT_BOOTSTRAP_SERVERS')
    api_key = os.getenv('CONFLUENT_API_KEY')
    api_secret = os.getenv('CONFLUENT_API_SECRET')
    
    print("🔗 Testing Confluent Cloud with kafka-python...")
    print(f"   Bootstrap: {bootstrap_servers}")
    print(f"   API Key: {api_key[:8]}...")
    
    try:
        # Test producer
        print("\n📤 Testing producer...")
        producer = KafkaProducer(
            bootstrap_servers=[bootstrap_servers],
            security_protocol='SASL_SSL',
            sasl_mechanism='PLAIN',
            sasl_plain_username=api_key,
            sasl_plain_password=api_secret,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            request_timeout_ms=30000,
            api_version=(2, 0, 0)
        )
        
        # Send a test message
        test_message = {
            'test': True,
            'timestamp': time.time(),
            'message': 'Test from kafka-python'
        }
        
        print("📤 Sending test message...")
        future = producer.send('financial-transactions', key='test', value=test_message)
        
        # Wait for send to complete
        record_metadata = future.get(timeout=30)
        print(f"✅ Message sent to topic: {record_metadata.topic}")
        print(f"   Partition: {record_metadata.partition}")
        print(f"   Offset: {record_metadata.offset}")
        
        producer.close()
        
        # Test consumer
        print("\n📥 Testing consumer...")
        consumer = KafkaConsumer(
            'financial-transactions',
            bootstrap_servers=bootstrap_servers,
            security_protocol='SASL_SSL',
            sasl_mechanism='PLAIN',
            sasl_plain_username=api_key,
            sasl_plain_password=api_secret,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=5000  # 5 second timeout
        )
        
        print("📥 Checking for messages...")
        message_count = 0
        for message in consumer:
            print(f"✅ Received message: {message.value}")
            message_count += 1
            if message_count >= 1:  # Just get one message to test
                break
        
        consumer.close()
        
        if message_count == 0:
            print("ℹ️  No new messages (this is normal)")
        
        print("\n🎉 kafka-python test successful!")
        return True
        
    except Exception as e:
        print(f"❌ kafka-python test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_kafka_python()
    exit(0 if success else 1)