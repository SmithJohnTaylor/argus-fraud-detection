#!/usr/bin/env python3
"""
List available topics in Confluent Cloud
"""

import os
from confluent_kafka.admin import AdminClient
from dotenv import load_dotenv

def list_topics():
    """List topics in Confluent Cloud"""
    
    load_dotenv()
    
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'ssl.endpoint.identification.algorithm': 'https',
    }
    
    try:
        admin_client = AdminClient(config)
        metadata = admin_client.list_topics(timeout=10)
        
        print(f"✅ Connected to cluster: {metadata.cluster_id}")
        print(f"📋 Available topics ({len(metadata.topics)}):")
        
        for topic_name, topic_metadata in metadata.topics.items():
            print(f"   - {topic_name} ({len(topic_metadata.partitions)} partitions)")
            
        # Check if our required topics exist
        required_topics = ['financial-transactions', 'ai-decisions', 'alerts']
        print(f"\n🔍 Required topics status:")
        for topic in required_topics:
            status = "✅ EXISTS" if topic in metadata.topics else "❌ MISSING"
            print(f"   - {topic}: {status}")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to list topics: {e}")
        return False

if __name__ == "__main__":
    list_topics()