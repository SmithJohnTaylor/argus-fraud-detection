#!/usr/bin/env python3
"""
Kafka Producer for Financial Transaction Simulation
Generates realistic financial transactions and sends them to Confluent Cloud
"""

import argparse
import json
import logging
import random
import signal
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransactionType(Enum):
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    TRANSFER = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Location:
    city: str
    state: str
    country: str
    latitude: float
    longitude: float
    timezone: str


@dataclass
class Transaction:
    transaction_id: str
    customer_id: str
    merchant_id: str
    merchant_name: str
    merchant_category: str
    amount: float
    currency: str
    transaction_type: str
    payment_method: str
    location: Location
    timestamp: str
    device_id: str
    ip_address: str
    risk_indicators: List[str]
    metadata: Dict[str, str]


class TransactionGenerator:
    """Generates realistic financial transactions with various risk patterns"""
    
    def __init__(self):
        # Customer pools
        self.customers = self._generate_customer_pool()
        
        # Merchant data
        self.merchants = {
            'grocery': [
                ('WHOLE_FOODS', 'Whole Foods Market'),
                ('KROGER', 'Kroger'),
                ('SAFEWAY', 'Safeway'),
                ('TRADER_JOES', 'Trader Joe\'s'),
                ('WALMART_GROCERY', 'Walmart Grocery')
            ],
            'restaurant': [
                ('MCDONALDS', 'McDonald\'s'),
                ('STARBUCKS', 'Starbucks'),
                ('SUBWAY', 'Subway'),
                ('CHIPOTLE', 'Chipotle Mexican Grill'),
                ('PANERA', 'Panera Bread')
            ],
            'gas_station': [
                ('SHELL', 'Shell'),
                ('EXXON', 'ExxonMobil'),
                ('CHEVRON', 'Chevron'),
                ('BP', 'BP'),
                ('TEXACO', 'Texaco')
            ],
            'retail': [
                ('AMAZON', 'Amazon'),
                ('TARGET', 'Target'),
                ('WALMART', 'Walmart'),
                ('BEST_BUY', 'Best Buy'),
                ('HOME_DEPOT', 'Home Depot')
            ],
            'high_risk': [
                ('CRYPTO_EXCHANGE', 'CryptoMax Exchange'),
                ('OFFSHORE_CASINO', 'Lucky777 Casino'),
                ('CASH_ADVANCE', 'QuickCash Advance'),
                ('PAWN_SHOP', 'Gold Rush Pawn'),
                ('MONEY_TRANSFER', 'FastMoney Transfer')
            ],
            'suspicious': [
                ('UNKNOWN_MERCHANT', 'Unknown Merchant'),
                ('TEMP_VENDOR', 'Temporary Vendor'),
                ('CASH_ONLY', 'Cash Only Store'),
                ('SHELL_COMPANY', 'ABC Trading LLC')
            ]
        }
        
        # Location data
        self.locations = {
            'domestic_safe': [
                Location('New York', 'NY', 'USA', 40.7128, -74.0060, 'America/New_York'),
                Location('Los Angeles', 'CA', 'USA', 34.0522, -118.2437, 'America/Los_Angeles'),
                Location('Chicago', 'IL', 'USA', 41.8781, -87.6298, 'America/Chicago'),
                Location('Houston', 'TX', 'USA', 29.7604, -95.3698, 'America/Chicago'),
                Location('Phoenix', 'AZ', 'USA', 33.4484, -112.0740, 'America/Phoenix'),
                Location('Philadelphia', 'PA', 'USA', 39.9526, -75.1652, 'America/New_York'),
                Location('San Antonio', 'TX', 'USA', 29.4241, -98.4936, 'America/Chicago'),
                Location('San Diego', 'CA', 'USA', 32.7157, -117.1611, 'America/Los_Angeles'),
                Location('Dallas', 'TX', 'USA', 32.7767, -96.7970, 'America/Chicago'),
                Location('Austin', 'TX', 'USA', 30.2672, -97.7431, 'America/Chicago')
            ],
            'domestic_medium': [
                Location('Las Vegas', 'NV', 'USA', 36.1699, -115.1398, 'America/Los_Angeles'),
                Location('Miami', 'FL', 'USA', 25.7617, -80.1918, 'America/New_York'),
                Location('Detroit', 'MI', 'USA', 42.3314, -83.0458, 'America/New_York'),
                Location('Memphis', 'TN', 'USA', 35.1495, -90.0490, 'America/Chicago'),
                Location('New Orleans', 'LA', 'USA', 29.9511, -90.0715, 'America/Chicago')
            ],
            'international_safe': [
                Location('London', '', 'GBR', 51.5074, -0.1278, 'Europe/London'),
                Location('Toronto', 'ON', 'CAN', 43.6532, -79.3832, 'America/Toronto'),
                Location('Paris', '', 'FRA', 48.8566, 2.3522, 'Europe/Paris'),
                Location('Tokyo', '', 'JPN', 35.6762, 139.6503, 'Asia/Tokyo'),
                Location('Sydney', 'NSW', 'AUS', -33.8688, 151.2093, 'Australia/Sydney')
            ],
            'international_high_risk': [
                Location('Lagos', '', 'NGA', 6.5244, 3.3792, 'Africa/Lagos'),
                Location('Bucharest', '', 'ROU', 44.4268, 26.1025, 'Europe/Bucharest'),
                Location('Caracas', '', 'VEN', 10.4806, -66.9036, 'America/Caracas'),
                Location('Dhaka', '', 'BGD', 23.8103, 90.4125, 'Asia/Dhaka'),
                Location('Karachi', '', 'PAK', 24.8607, 67.0011, 'Asia/Karachi')
            ],
            'unknown': [
                Location('Unknown', '', 'XXX', 0.0, 0.0, 'UTC')
            ]
        }
        
        # Payment methods with risk levels
        self.payment_methods = {
            'low_risk': ['CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER'],
            'medium_risk': ['DIGITAL_WALLET', 'PREPAID_CARD', 'MOBILE_PAYMENT'],
            'high_risk': ['CRYPTOCURRENCY', 'MONEY_ORDER', 'WIRE_TRANSFER', 'CASH']
        }
    
    def _generate_customer_pool(self) -> List[str]:
        """Generate a pool of customer IDs"""
        return [f"CUST_{i:06d}" for i in range(1, 10001)]
    
    def _get_random_merchant(self, risk_level: RiskLevel) -> Tuple[str, str, str]:
        """Get random merchant based on risk level"""
        if risk_level == RiskLevel.CRITICAL:
            category = random.choice(['high_risk', 'suspicious'])
        elif risk_level == RiskLevel.HIGH:
            category = random.choice(['high_risk', 'retail'])
        elif risk_level == RiskLevel.MEDIUM:
            category = random.choice(['retail', 'restaurant'])
        else:  # LOW risk
            category = random.choice(['grocery', 'gas_station', 'restaurant'])
        
        merchant_id, merchant_name = random.choice(self.merchants[category])
        return merchant_id, merchant_name, category
    
    def _get_random_location(self, risk_level: RiskLevel) -> Location:
        """Get random location based on risk level"""
        if risk_level == RiskLevel.CRITICAL:
            location_type = random.choice(['international_high_risk', 'unknown'])
        elif risk_level == RiskLevel.HIGH:
            location_type = random.choice(['international_high_risk', 'international_safe', 'domestic_medium'])
        elif risk_level == RiskLevel.MEDIUM:
            location_type = random.choice(['domestic_medium', 'international_safe', 'domestic_safe'])
        else:  # LOW risk
            location_type = 'domestic_safe'
        
        return random.choice(self.locations[location_type])
    
    def _get_transaction_amount(self, risk_level: RiskLevel, merchant_category: str) -> float:
        """Generate transaction amount based on risk level and merchant category"""
        # Base amounts by merchant category
        base_amounts = {
            'grocery': (15, 150),
            'restaurant': (8, 80),
            'gas_station': (20, 100),
            'retail': (25, 500),
            'high_risk': (100, 50000),
            'suspicious': (500, 25000)
        }
        
        min_amount, max_amount = base_amounts.get(merchant_category, (10, 1000))
        
        if risk_level == RiskLevel.CRITICAL:
            # Very large amounts or suspiciously round numbers
            if random.random() < 0.3:
                return round(random.uniform(10000, 100000), 2)
            else:
                return float(random.choice([5000, 10000, 15000, 20000, 25000]))
        elif risk_level == RiskLevel.HIGH:
            # Large amounts
            return round(random.uniform(max(1000, min_amount), max_amount * 5), 2)
        elif risk_level == RiskLevel.MEDIUM:
            # Slightly elevated amounts
            return round(random.uniform(min_amount, max_amount * 2), 2)
        else:
            # Normal amounts
            return round(random.uniform(min_amount, max_amount), 2)
    
    def _get_payment_method(self, risk_level: RiskLevel) -> str:
        """Get payment method based on risk level"""
        if risk_level == RiskLevel.CRITICAL:
            return random.choice(self.payment_methods['high_risk'])
        elif risk_level == RiskLevel.HIGH:
            return random.choice(self.payment_methods['medium_risk'] + self.payment_methods['high_risk'])
        elif risk_level == RiskLevel.MEDIUM:
            return random.choice(self.payment_methods['low_risk'] + self.payment_methods['medium_risk'])
        else:
            return random.choice(self.payment_methods['low_risk'])
    
    def _get_transaction_time(self, risk_level: RiskLevel) -> datetime:
        """Generate transaction timestamp with risk-based timing"""
        base_time = datetime.now()
        
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # Higher chance of unusual hours
            if random.random() < 0.4:
                # Very late night (2-5 AM)
                hour = random.randint(2, 5)
                minute = random.randint(0, 59)
                base_time = base_time.replace(hour=hour, minute=minute)
        elif risk_level == RiskLevel.MEDIUM:
            # Slightly off-hours
            if random.random() < 0.2:
                hour = random.choice([23, 0, 1, 6, 7])
                minute = random.randint(0, 59)
                base_time = base_time.replace(hour=hour, minute=minute)
        
        # Add some random offset
        offset_minutes = random.randint(-60, 60)
        return base_time + timedelta(minutes=offset_minutes)
    
    def _generate_risk_indicators(self, risk_level: RiskLevel, amount: float, location: Location, 
                                 merchant_category: str, timestamp: datetime) -> List[str]:
        """Generate risk indicators based on transaction characteristics"""
        indicators = []
        
        if amount > 10000:
            indicators.append("HIGH_AMOUNT")
        if amount == round(amount) and amount > 1000:
            indicators.append("ROUND_AMOUNT")
        
        if location.country != 'USA':
            indicators.append("INTERNATIONAL_TRANSACTION")
        if location.country in ['XXX', 'NGA', 'ROU', 'VEN', 'BGD', 'PAK']:
            indicators.append("HIGH_RISK_COUNTRY")
        
        hour = timestamp.hour
        if 2 <= hour <= 5:
            indicators.append("UNUSUAL_HOUR")
        elif hour >= 23 or hour <= 1:
            indicators.append("LATE_NIGHT")
        
        if merchant_category in ['high_risk', 'suspicious']:
            indicators.append("HIGH_RISK_MERCHANT")
        
        if risk_level == RiskLevel.CRITICAL:
            indicators.extend(["CRITICAL_RISK", "MANUAL_REVIEW_REQUIRED"])
        elif risk_level == RiskLevel.HIGH:
            indicators.append("HIGH_RISK")
        
        return indicators
    
    def generate_transaction(self, risk_level: Optional[RiskLevel] = None) -> Transaction:
        """Generate a single transaction"""
        if risk_level is None:
            # Weight distribution: 70% low, 20% medium, 8% high, 2% critical
            weights = [0.70, 0.20, 0.08, 0.02]
            risk_level = random.choices(list(RiskLevel), weights=weights)[0]
        
        # Generate basic info
        transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        customer_id = random.choice(self.customers)
        
        # Get merchant info
        merchant_id, merchant_name, merchant_category = self._get_random_merchant(risk_level)
        
        # Get location
        location = self._get_random_location(risk_level)
        
        # Get amount
        amount = self._get_transaction_amount(risk_level, merchant_category)
        
        # Get payment method
        payment_method = self._get_payment_method(risk_level)
        
        # Get timestamp
        timestamp = self._get_transaction_time(risk_level)
        
        # Generate risk indicators
        risk_indicators = self._generate_risk_indicators(
            risk_level, amount, location, merchant_category, timestamp
        )
        
        # Generate additional fields
        device_id = f"DEV_{random.randint(100000, 999999)}"
        ip_address = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        # Transaction type
        transaction_type = random.choices(
            list(TransactionType),
            weights=[0.85, 0.05, 0.05, 0.03, 0.02]
        )[0].value
        
        # Currency
        currency = 'USD' if location.country == 'USA' else random.choice(['USD', 'EUR', 'GBP', 'CAD', 'AUD'])
        
        # Metadata
        metadata = {
            'risk_level': risk_level.value,
            'merchant_category': merchant_category,
            'location_type': 'domestic' if location.country == 'USA' else 'international',
            'generated_at': datetime.now().isoformat()
        }
        
        return Transaction(
            transaction_id=transaction_id,
            customer_id=customer_id,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            merchant_category=merchant_category,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            payment_method=payment_method,
            location=location,
            timestamp=timestamp.isoformat(),
            device_id=device_id,
            ip_address=ip_address,
            risk_indicators=risk_indicators,
            metadata=metadata
        )


class ConfluentCloudProducer:
    """Kafka producer for Confluent Cloud"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        # Extract topic before creating producer (topic is not a producer config)
        self.topic = config.pop('topic', 'financial-transactions')
        self.producer = Producer(config)
        self.messages_sent = 0
        self.messages_failed = 0
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Initialized producer for topic: {self.topic}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery"""
        if err:
            self.messages_failed += 1
            logger.error(f"Message delivery failed: {err}")
        else:
            self.messages_sent += 1
            if self.messages_sent % 100 == 0:
                logger.info(f"Messages sent: {self.messages_sent}")
    
    def create_topic_if_not_exists(self):
        """Create topic if it doesn't exist (for development)"""
        try:
            admin_client = AdminClient({
                'bootstrap.servers': self.config['bootstrap.servers'],
                'security.protocol': self.config.get('security.protocol', 'SASL_SSL'),
                'sasl.mechanism': self.config.get('sasl.mechanism', 'PLAIN'),
                'sasl.username': self.config.get('sasl.username', ''),
                'sasl.password': self.config.get('sasl.password', ''),
                'ssl.endpoint.identification.algorithm': self.config.get('ssl.endpoint.identification.algorithm', 'https')
            })
            
            # Note: Topic creation might not be allowed in Confluent Cloud
            # This is mainly for development environments
            new_topic = NewTopic(self.topic, num_partitions=3, replication_factor=3)
            fs = admin_client.create_topics([new_topic])
            
            for topic, f in fs.items():
                try:
                    f.result()
                    logger.info(f"Topic {topic} created successfully")
                except Exception as e:
                    logger.info(f"Topic {topic} might already exist: {e}")
                    
        except Exception as e:
            logger.warning(f"Could not create topic (this is normal for Confluent Cloud): {e}")
    
    def send_transaction(self, transaction: Transaction):
        """Send a transaction to Kafka"""
        try:
            # Convert transaction to JSON
            message = json.dumps(asdict(transaction), default=str)
            
            # Send to Kafka
            self.producer.produce(
                topic=self.topic,
                key=transaction.transaction_id,
                value=message,
                callback=self._delivery_callback
            )
            
            # Poll for delivery reports
            self.producer.poll(0)
            
        except Exception as e:
            logger.error(f"Failed to send transaction {transaction.transaction_id}: {e}")
            self.messages_failed += 1
    
    def run_generator(self, rate: float, duration: Optional[int] = None, 
                     pattern: str = 'mixed'):
        """Run the transaction generator"""
        generator = TransactionGenerator()
        
        start_time = time.time()
        interval = 1.0 / rate if rate > 0 else 1.0
        
        logger.info(f"Starting transaction generation at {rate} transactions/second")
        if duration:
            logger.info(f"Will run for {duration} seconds")
        
        try:
            while self.running:
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    logger.info("Duration reached, stopping...")
                    break
                
                # Generate transaction based on pattern
                if pattern == 'high_risk':
                    risk_level = random.choices(
                        [RiskLevel.HIGH, RiskLevel.CRITICAL],
                        weights=[0.7, 0.3]
                    )[0]
                elif pattern == 'normal':
                    risk_level = random.choices(
                        [RiskLevel.LOW, RiskLevel.MEDIUM],
                        weights=[0.8, 0.2]
                    )[0]
                else:  # mixed
                    risk_level = None
                
                transaction = generator.generate_transaction(risk_level)
                self.send_transaction(transaction)
                
                # Wait for next transaction
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the producer"""
        logger.info("Shutting down producer...")
        
        # Wait for any outstanding messages to be delivered
        remaining = self.producer.flush(30)
        if remaining > 0:
            logger.warning(f"{remaining} messages were not delivered")
        
        logger.info(f"Final stats - Sent: {self.messages_sent}, Failed: {self.messages_failed}")


def load_config(config_file: Optional[str] = None) -> Dict[str, str]:
    """Load Confluent Cloud configuration"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Use minimal configuration that we know works
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanism': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'topic': os.getenv('KAFKA_TOPIC_TRANSACTIONS', 'financial-transactions')
    }
    
    # Load from config file if provided
    if config_file:
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        config[key] = value
        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
    
    # Validate required Confluent Cloud config
    required_keys = ['bootstrap.servers', 'sasl.username', 'sasl.password']
    for key in required_keys:
        if not config.get(key):
            logger.error(f"Missing required Confluent Cloud configuration: {key}")
            logger.error("Please ensure CONFLUENT_BOOTSTRAP_SERVERS, CONFLUENT_API_KEY, and CONFLUENT_API_SECRET are set")
            sys.exit(1)
    
    return config


def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Financial Transaction Generator for Confluent Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 transactions per second for 60 seconds
  python generator.py --rate 10 --duration 60
  
  # Generate high-risk transactions only
  python generator.py --rate 5 --pattern high_risk
  
  # Use custom config file
  python generator.py --config confluent.properties --rate 2
        """
    )
    
    parser.add_argument(
        '--rate', '-r',
        type=float,
        default=1.0,
        help='Transactions per second (default: 1.0)'
    )
    
    parser.add_argument(
        '--duration', '-d',
        type=int,
        help='Duration in seconds (default: infinite)'
    )
    
    parser.add_argument(
        '--pattern', '-p',
        choices=['mixed', 'normal', 'high_risk'],
        default='mixed',
        help='Transaction pattern (default: mixed)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to Confluent Cloud properties file'
    )
    
    parser.add_argument(
        '--create-topic',
        action='store_true',
        help='Attempt to create topic if it doesn\'t exist'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = load_config(args.config)
    
    # Create and run producer
    producer = ConfluentCloudProducer(config)
    
    if args.create_topic:
        producer.create_topic_if_not_exists()
    
    producer.run_generator(
        rate=args.rate,
        duration=args.duration,
        pattern=args.pattern
    )


if __name__ == "__main__":
    main()