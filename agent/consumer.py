import json
import os
from kafka import KafkaConsumer
from together_client import TogetherAIAgent
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransactionConsumer:
    def __init__(self, kafka_config: dict, together_api_key: str = None):
        self.consumer = KafkaConsumer(
            kafka_config.get('topic', 'financial-transactions'),
            bootstrap_servers=kafka_config.get('bootstrap_servers', 'localhost:9092'),
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            key_deserializer=lambda x: x.decode('utf-8') if x else None,
            group_id=kafka_config.get('group_id', 'fraud-detection-group'),
            auto_offset_reset='latest'
        )
        
        self.agent = TogetherAIAgent(api_key=together_api_key)
        self.processed_count = 0
        
    def start_consuming(self):
        """Start consuming transactions and analyzing them"""
        logger.info("Starting transaction consumer...")
        
        try:
            for message in self.consumer:
                transaction = message.value
                logger.info(f"Processing transaction: {transaction.get('transaction_id')}")
                
                # Analyze transaction with Together AI
                analysis_result = self.agent.analyze_transaction(transaction)
                
                # Log results
                self._log_analysis(analysis_result)
                
                # Handle high-risk transactions
                self._handle_risk_response(analysis_result, transaction)
                
                self.processed_count += 1
                
                if self.processed_count % 10 == 0:
                    logger.info(f"Processed {self.processed_count} transactions")
                    
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            self.consumer.close()
            logger.info(f"Consumer stopped. Processed {self.processed_count} transactions")
    
    def _log_analysis(self, analysis_result: dict):
        """Log analysis results"""
        transaction_id = analysis_result.get('transaction_id')
        risk_level = analysis_result.get('risk_level', 'UNKNOWN')
        
        logger.info(f"Transaction {transaction_id}: Risk Level = {risk_level}")
        
        if 'analysis' in analysis_result:
            if 'risk_score' in analysis_result['analysis']:
                logger.info(f"  Risk Score: {analysis_result['analysis']['risk_score']}")
            
            if 'is_suspicious' in analysis_result['analysis']:
                logger.info(f"  Suspicious: {analysis_result['analysis']['is_suspicious']}")
        
        if analysis_result.get('recommendations'):
            logger.info(f"  Recommendations: {', '.join(analysis_result['recommendations'])}")
    
    def _handle_risk_response(self, analysis_result: dict, original_transaction: dict):
        """Handle response based on risk level"""
        risk_level = analysis_result.get('risk_level', 'UNKNOWN')
        transaction_id = analysis_result.get('transaction_id')
        
        if risk_level in ['HIGH', 'CRITICAL']:
            logger.warning(f"HIGH RISK TRANSACTION DETECTED: {transaction_id}")
            
            # In a real system, you might:
            # - Block the transaction
            # - Send to manual review queue
            # - Trigger additional verification
            # - Update user risk profile
            
        elif risk_level == 'MEDIUM':
            logger.info(f"Medium risk transaction flagged: {transaction_id}")
            
            # In a real system, you might:
            # - Require additional authentication
            # - Add to monitoring list
            # - Send customer notification


if __name__ == "__main__":
    kafka_config = {
        'bootstrap_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'topic': os.getenv('KAFKA_TOPIC', 'financial-transactions'),
        'group_id': os.getenv('KAFKA_GROUP_ID', 'fraud-detection-group')
    }
    
    consumer = TransactionConsumer(
        kafka_config=kafka_config,
        together_api_key=os.getenv('TOGETHER_API_KEY')
    )
    
    consumer.start_consuming()