#!/usr/bin/env python3
"""
Pytest configuration and fixtures for E2E testing
"""

import asyncio
import os
import pytest
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def kafka_config():
    """Kafka configuration for testing"""
    return {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'client.id': 'e2e-test-client'
    }


@pytest.fixture(scope="session")
def test_environment():
    """Test environment configuration"""
    return {
        'together_api_key': os.getenv('TOGETHER_API_KEY', 'test_placeholder_key'),
        'kafka_bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'test_timeout': int(os.getenv('TEST_TIMEOUT', '60')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }


@pytest.fixture
def test_transaction():
    """Sample test transaction"""
    from datetime import datetime
    import uuid
    
    return {
        'transaction_id': f'TEST_{uuid.uuid4().hex[:8]}',
        'customer_id': 'TEST_CUSTOMER_001',
        'amount': 100.00,
        'currency': 'USD',
        'merchant_id': 'TEST_MERCHANT',
        'merchant_name': 'Test Merchant',
        'merchant_category': 'retail',
        'location': {
            'city': 'Test City',
            'state': 'TC',
            'country': 'USA',
            'latitude': 40.0,
            'longitude': -74.0,
            'timezone': 'America/New_York'
        },
        'payment_method': 'CREDIT_CARD',
        'timestamp': datetime.now().isoformat(),
        'device_id': 'TEST_DEVICE',
        'ip_address': '192.168.1.100'
    }