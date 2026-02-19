import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime
from enum import Enum
from confluent_kafka import Producer


class AlertChannel(Enum):
    DATABASE = "database"
    CONSOLE = "console"
    KAFKA = "kafka"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class NotificationTools:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # In-memory storage for demo (would be database in production)
        self.alerts = []
        
        # Initialize Kafka producer for alerts
        self._init_kafka_producer()
        self.alert_rules = {
            RiskLevel.CRITICAL: [AlertChannel.DATABASE, AlertChannel.CONSOLE, AlertChannel.KAFKA],
            RiskLevel.HIGH: [AlertChannel.DATABASE, AlertChannel.CONSOLE, AlertChannel.KAFKA],
            RiskLevel.MEDIUM: [AlertChannel.DATABASE, AlertChannel.KAFKA],
            RiskLevel.LOW: [AlertChannel.DATABASE]
        }
        
        # Alert configurations
        self.config = {
            'database': {
                'enabled': True,
                'storage': 'in_memory'  # Would be actual database in production
            },
            'console': {
                'enabled': True,
                'log_level': 'WARNING'
            }
        }
    
    def send_alert(self, transaction_id: str, risk_level: str, reason: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send fraud alert through appropriate channels"""
        
        try:
            risk_enum = RiskLevel(risk_level.upper())
        except ValueError:
            risk_enum = RiskLevel.MEDIUM
        
        alert = self._create_alert(transaction_id, risk_enum, reason, additional_data)
        
        # Store alert
        self.alerts.append(alert)
        
        # Determine channels to use
        channels = self.alert_rules.get(risk_enum, [AlertChannel.DATABASE])
        
        results = {}
        for channel in channels:
            try:
                if channel == AlertChannel.DATABASE:
                    results['database'] = self._store_alert(alert)
                elif channel == AlertChannel.CONSOLE:
                    results['console'] = self._send_console_alert(alert)
                elif channel == AlertChannel.KAFKA:
                    results['kafka'] = self._send_kafka_alert(alert)
                    
            except Exception as e:
                self.logger.error(f"Failed to send alert via {channel.value}: {e}")
                results[channel.value] = {"status": "failed", "error": str(e)}
        
        return {
            "alert_id": alert['alert_id'],
            "status": "sent",
            "channels": results,
            "timestamp": alert['timestamp']
        }
    
    def _create_alert(self, transaction_id: str, risk_level: RiskLevel, reason: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create alert object"""
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{transaction_id[:8]}"
        
        alert = {
            "alert_id": alert_id,
            "transaction_id": transaction_id,
            "risk_level": risk_level.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "status": "active",
            "additional_data": additional_data or {}
        }
        
        return alert
    
    def _send_console_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Send console alert (log output)"""
        if not self.config['console']['enabled']:
            return {"status": "disabled"}
        
        # Log alert to console with appropriate level
        if alert['risk_level'] in ['CRITICAL', 'HIGH']:
            self.logger.error(f"FRAUD ALERT: {alert['alert_id']} - {alert['risk_level']} risk transaction {alert['transaction_id']} - {alert['reason']}")
        else:
            self.logger.warning(f"FRAUD ALERT: {alert['alert_id']} - {alert['risk_level']} risk transaction {alert['transaction_id']} - {alert['reason']}")
        
        return {
            "status": "logged",
            "level": "ERROR" if alert['risk_level'] in ['CRITICAL', 'HIGH'] else "WARNING",
            "timestamp": datetime.now().isoformat()
        }
    
    def _store_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Store alert in database (simulated)"""
        # In production, would store in database
        self.logger.info(f"DATABASE: Stored alert {alert['alert_id']}")
        
        return {
            "status": "stored",
            "database": "fraud_alerts_db",
            "table": "alerts",
            "timestamp": datetime.now().isoformat()
        }
    
    def _init_kafka_producer(self):
        """Initialize Kafka producer for alert publishing"""
        try:
            producer_config = {
                'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
                'security.protocol': os.getenv('CONFLUENT_SECURITY_PROTOCOL', 'SASL_SSL'),
                'sasl.mechanism': os.getenv('CONFLUENT_SASL_MECHANISMS', 'PLAIN'),
                'sasl.username': os.getenv('CONFLUENT_API_KEY'),
                'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
                'ssl.endpoint.identification.algorithm': os.getenv('CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM', 'https'),
                'client.id': 'fraud-alert-producer'
            }
            
            self.kafka_producer = Producer(producer_config)
            self.alerts_topic = os.getenv('KAFKA_TOPIC_ALERTS', 'alerts')
            self.logger.info(f"Kafka producer initialized for alerts topic: {self.alerts_topic}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka producer for alerts: {e}")
            self.kafka_producer = None
    
    def _send_kafka_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Send alert to Kafka alerts topic"""
        if not self.kafka_producer:
            return {"status": "failed", "error": "Kafka producer not initialized"}
        
        try:
            # Prepare alert message for Kafka
            alert_message = {
                "alert_id": alert["alert_id"],
                "transaction_id": alert["transaction_id"], 
                "risk_level": alert["risk_level"],
                "reason": alert["reason"],
                "timestamp": alert["timestamp"],
                "status": alert["status"],
                "additional_data": alert["additional_data"]
            }
            
            # Publish to Kafka
            self.kafka_producer.produce(
                topic=self.alerts_topic,
                key=alert["transaction_id"],
                value=json.dumps(alert_message),
                callback=self._kafka_delivery_callback
            )
            
            # Flush to ensure delivery
            self.kafka_producer.flush(timeout=1.0)
            
            self.logger.info(f"Alert {alert['alert_id']} published to Kafka topic {self.alerts_topic}")
            
            return {
                "status": "published",
                "topic": self.alerts_topic,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to publish alert to Kafka: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _kafka_delivery_callback(self, err, msg):
        """Callback for Kafka message delivery"""
        if err:
            self.logger.error(f"Alert delivery failed: {err}")
        else:
            self.logger.debug(f"Alert delivered to {msg.topic()} partition {msg.partition()}")
    
    def get_recent_alerts(self, hours: int = 24, risk_levels: List[str] = None) -> List[Dict[str, Any]]:
        """Get recent alerts within specified timeframe"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_alerts = []
        for alert in self.alerts:
            try:
                alert_time = datetime.fromisoformat(alert['timestamp'])
                if alert_time >= cutoff_time:
                    if risk_levels is None or alert['risk_level'] in risk_levels:
                        recent_alerts.append(alert)
            except:
                continue
        
        return sorted(recent_alerts, key=lambda x: x['timestamp'], reverse=True)
    
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        recent_alerts = self.get_recent_alerts(hours)
        
        stats = {
            "total_alerts": len(recent_alerts),
            "by_risk_level": {},
            "timeframe_hours": hours,
            "generated_at": datetime.now().isoformat()
        }
        
        for level in RiskLevel:
            count = len([a for a in recent_alerts if a['risk_level'] == level.value])
            stats["by_risk_level"][level.value] = count
        
        return stats