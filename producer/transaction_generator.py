import json
import random
import time
from datetime import datetime
from typing import Dict, Any
from dataclasses import dataclass, asdict
from kafka import KafkaProducer
import uuid


@dataclass
class Transaction:
    transaction_id: str
    user_id: str
    merchant_id: str
    amount: float
    currency: str
    transaction_type: str
    timestamp: str
    location: Dict[str, Any]
    payment_method: str
    risk_score: float = 0.0
    
    
class TransactionGenerator:
    def __init__(self, kafka_config: Dict[str, Any]):
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_config.get('bootstrap_servers', 'localhost:9092'),
            value_serializer=lambda x: json.dumps(x).encode('utf-8'),
            key_serializer=lambda x: x.encode('utf-8') if x else None
        )
        self.topic = kafka_config.get('topic', 'financial-transactions')
        
    def generate_transaction(self) -> Transaction:
        merchants = [
            'AMAZON', 'WALMART', 'TARGET', 'STARBUCKS', 'MCDONALDS',
            'SHELL', 'EXXON', 'GROCERY_STORE', 'RESTAURANT', 'GAS_STATION'
        ]
        
        currencies = ['USD', 'EUR', 'GBP', 'JPY']
        transaction_types = ['PURCHASE', 'REFUND', 'TRANSFER', 'WITHDRAWAL']
        payment_methods = ['CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'DIGITAL_WALLET']
        
        locations = [
            {'city': 'New York', 'state': 'NY', 'country': 'USA', 'lat': 40.7128, 'lon': -74.0060},
            {'city': 'Los Angeles', 'state': 'CA', 'country': 'USA', 'lat': 34.0522, 'lon': -118.2437},
            {'city': 'Chicago', 'state': 'IL', 'country': 'USA', 'lat': 41.8781, 'lon': -87.6298},
            {'city': 'London', 'state': '', 'country': 'UK', 'lat': 51.5074, 'lon': -0.1278},
            {'city': 'Tokyo', 'state': '', 'country': 'Japan', 'lat': 35.6762, 'lon': 139.6503}
        ]
        
        # Generate higher risk scenarios occasionally
        is_high_risk = random.random() < 0.1
        
        if is_high_risk:
            amount = random.uniform(5000, 50000)
            risk_score = random.uniform(0.7, 1.0)
        else:
            amount = random.uniform(1, 1000)
            risk_score = random.uniform(0.0, 0.3)
            
        return Transaction(
            transaction_id=str(uuid.uuid4()),
            user_id=f"user_{random.randint(1000, 9999)}",
            merchant_id=random.choice(merchants),
            amount=round(amount, 2),
            currency=random.choice(currencies),
            transaction_type=random.choice(transaction_types),
            timestamp=datetime.now().isoformat(),
            location=random.choice(locations),
            payment_method=random.choice(payment_methods),
            risk_score=risk_score
        )
    
    def send_transaction(self, transaction: Transaction):
        try:
            future = self.producer.send(
                self.topic,
                key=transaction.transaction_id,
                value=asdict(transaction)
            )
            future.get(timeout=10)
            print(f"Sent transaction {transaction.transaction_id}")
        except Exception as e:
            print(f"Failed to send transaction: {e}")
    
    def start_generating(self, interval: float = 1.0, count: int = None):
        """Start generating transactions at specified interval"""
        transactions_sent = 0
        
        try:
            while True:
                if count and transactions_sent >= count:
                    break
                    
                transaction = self.generate_transaction()
                self.send_transaction(transaction)
                transactions_sent += 1
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\nStopping transaction generator...")
        finally:
            self.producer.close()
            print(f"Generated {transactions_sent} transactions")


if __name__ == "__main__":
    import os
    
    kafka_config = {
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'topic': os.getenv('KAFKA_TOPIC', 'financial-transactions')
    }
    
    generator = TransactionGenerator(kafka_config)
    generator.start_generating(interval=2.0)