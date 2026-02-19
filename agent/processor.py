#!/usr/bin/env python3
"""
AI-Powered Financial Transaction Processor
Consumes transactions from Kafka, analyzes with Together AI, and produces decisions
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import traceback
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import random

import aiohttp
from confluent_kafka import Consumer, Producer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('agent_processor.log')
    ]
)
logger = logging.getLogger(__name__)

# Risk threshold constants
CRITICAL_RISK_THRESHOLD = 0.80
HIGH_RISK_THRESHOLD = 0.60
MEDIUM_RISK_THRESHOLD = 0.40

# Create specialized loggers
tool_logger = logging.getLogger('tools')
reasoning_logger = logging.getLogger('reasoning')
api_logger = logging.getLogger('together_ai')


class DecisionType(Enum):
    APPROVE = "APPROVE"
    DECLINE = "DECLINE"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    ADDITIONAL_AUTH = "ADDITIONAL_AUTH"


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class AIDecision:
    decision_id: str
    transaction_id: str
    customer_id: str
    decision_type: str
    risk_level: str
    confidence_score: float
    reasoning: str
    tool_calls_made: List[str]
    tool_results: Dict[str, Any]
    processing_time_ms: int
    model_used: str
    timestamp: str
    metadata: Dict[str, Any]


class TransactionHistoryTool:
    """Tool for checking customer transaction history"""
    
    def __init__(self):
        # In production, this would connect to a real database
        self.transaction_cache = {}
        self.customer_profiles = {}
    
    async def check_transaction_history(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """Check customer's transaction history for patterns"""
        tool_logger.info(f"Checking transaction history for customer {customer_id} (last {days} days)")
        
        try:
            # Generate realistic historical data
            profile = self._get_or_create_customer_profile(customer_id)
            history = self._generate_transaction_history(customer_id, days, profile)
            
            result = {
                "customer_id": customer_id,
                "days_analyzed": days,
                "total_transactions": history["total_transactions"],
                "total_amount": history["total_amount"],
                "average_amount": history["average_amount"],
                "transaction_frequency": history["transaction_frequency"],
                "common_merchants": history["common_merchants"],
                "common_locations": history["common_locations"],
                "unusual_patterns": history["unusual_patterns"],
                "velocity_alerts": history["velocity_alerts"],
                "previous_declines": history["previous_declines"],
                "account_age_days": profile["account_age_days"],
                "risk_score_history": profile["risk_score_history"]
            }
            
            tool_logger.info(f"Transaction history analysis complete for {customer_id}: "
                           f"{result['total_transactions']} transactions, "
                           f"avg amount ${result['average_amount']:.2f}")
            
            return result
            
        except Exception as e:
            tool_logger.error(f"Error checking transaction history for {customer_id}: {e}")
            return {"error": str(e), "customer_id": customer_id}
    
    def _get_or_create_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get or create customer profile"""
        if customer_id not in self.customer_profiles:
            # Generate realistic customer profile
            account_age = random.randint(30, 2000)  # days
            risk_scores = [round(random.uniform(0.1, 0.4), 3) for _ in range(10)]
            
            self.customer_profiles[customer_id] = {
                "customer_id": customer_id,
                "account_age_days": account_age,
                "risk_score_history": risk_scores,
                "preferred_merchants": random.sample([
                    "STARBUCKS", "WALMART", "AMAZON", "SHELL", "GROCERY_STORE"
                ], k=random.randint(2, 4)),
                "typical_locations": random.sample([
                    "New York, NY, USA", "Los Angeles, CA, USA", "Chicago, IL, USA"
                ], k=random.randint(1, 2))
            }
        
        return self.customer_profiles[customer_id]
    
    def _generate_transaction_history(self, customer_id: str, days: int, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic transaction history"""
        # Base transaction patterns
        daily_avg_transactions = random.uniform(1.5, 5.0)
        total_transactions = int(days * daily_avg_transactions)
        
        # Amount patterns
        avg_amount = random.uniform(45, 200)
        total_amount = total_transactions * avg_amount * random.uniform(0.8, 1.2)
        
        # Unusual patterns detection
        unusual_patterns = []
        if random.random() < 0.15:
            unusual_patterns.append("Large transaction spike last week")
        if random.random() < 0.10:
            unusual_patterns.append("Unusual late-night activity")
        if random.random() < 0.08:
            unusual_patterns.append("Multiple international transactions")
        
        # Velocity alerts
        velocity_alerts = []
        if random.random() < 0.12:
            velocity_alerts.append("5 transactions in 1 hour yesterday")
        if random.random() < 0.05:
            velocity_alerts.append("High-value transactions above normal pattern")
        
        return {
            "total_transactions": total_transactions,
            "total_amount": round(total_amount, 2),
            "average_amount": round(total_amount / max(total_transactions, 1), 2),
            "transaction_frequency": round(daily_avg_transactions, 2),
            "common_merchants": profile["preferred_merchants"],
            "common_locations": profile["typical_locations"],
            "unusual_patterns": unusual_patterns,
            "velocity_alerts": velocity_alerts,
            "previous_declines": random.randint(0, 3)
        }


class RiskCalculatorTool:
    """Tool for calculating comprehensive risk scores"""
    
    async def calculate_risk_score(self, transaction: Dict[str, Any], 
                                 customer_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate multi-factor risk score"""
        tool_logger.info(f"Calculating risk score for transaction {transaction.get('transaction_id')}")
        
        try:
            risk_factors = {}
            
            # Amount risk
            amount = float(transaction.get('amount', 0))
            risk_factors['amount_risk'] = self._calculate_amount_risk(amount, customer_history)
            
            # Location risk
            location = transaction.get('location', {})
            risk_factors['location_risk'] = self._calculate_location_risk(location)
            
            # Merchant risk
            merchant = transaction.get('merchant_id', '')
            risk_factors['merchant_risk'] = self._calculate_merchant_risk(merchant)
            
            # Timing risk
            timestamp = transaction.get('timestamp', '')
            risk_factors['timing_risk'] = self._calculate_timing_risk(timestamp)
            
            # Customer behavior risk
            risk_factors['behavior_risk'] = self._calculate_behavior_risk(customer_history)
            
            # Payment method risk
            payment_method = transaction.get('payment_method', '')
            risk_factors['payment_method_risk'] = self._calculate_payment_method_risk(payment_method)
            
            # Calculate composite score
            weights = {
                'amount_risk': 0.25,
                'location_risk': 0.20,
                'merchant_risk': 0.15,
                'timing_risk': 0.15,
                'behavior_risk': 0.15,
                'payment_method_risk': 0.10
            }
            
            composite_score = sum(
                risk_factors[factor] * weights[factor] 
                for factor in weights
            )
            
            # Determine risk level
            if composite_score >= CRITICAL_RISK_THRESHOLD:
                risk_level = RiskLevel.CRITICAL.value
            elif composite_score >= HIGH_RISK_THRESHOLD:
                risk_level = RiskLevel.HIGH.value
            elif composite_score >= MEDIUM_RISK_THRESHOLD:
                risk_level = RiskLevel.MEDIUM.value
            else:
                risk_level = RiskLevel.LOW.value
            
            result = {
                "transaction_id": transaction.get('transaction_id'),
                "composite_risk_score": round(composite_score, 3),
                "risk_level": risk_level,
                "risk_factors": {k: round(v, 3) for k, v in risk_factors.items()},
                "confidence": self._calculate_confidence(customer_history),
                "recommendations": self._get_risk_recommendations(risk_level, composite_score)
            }
            
            tool_logger.info(f"Risk score calculated: {composite_score:.3f} ({risk_level}) "
                           f"for transaction {transaction.get('transaction_id')}")
            
            return result
            
        except Exception as e:
            tool_logger.error(f"Error calculating risk score: {e}")
            return {"error": str(e), "transaction_id": transaction.get('transaction_id')}
    
    def _calculate_amount_risk(self, amount: float, history: Optional[Dict[str, Any]]) -> float:
        """Calculate risk based on transaction amount"""
        if amount <= 0:
            return 0.5
        
        # Base risk increases with amount
        base_risk = min(amount / 10000, 0.6)
        
        # Compare with customer history
        if history and history.get('average_amount'):
            avg_amount = history['average_amount']
            if amount > avg_amount * 5:
                base_risk += 0.3
            elif amount > avg_amount * 3:
                base_risk += 0.2
        
        # Round amounts are suspicious for large transactions
        if amount > 1000 and amount == int(amount):
            base_risk += 0.1
        
        return min(base_risk, 1.0)
    
    def _calculate_location_risk(self, location: Dict[str, Any]) -> float:
        """Calculate risk based on location"""
        country = location.get('country', '').upper()
        
        high_risk_countries = ['XXX', 'NGA', 'ROU', 'VEN', 'BGD', 'PAK', 'IRN', 'PRK']
        medium_risk_countries = ['RUS', 'CHN', 'TUR', 'MEX', 'BRA']
        
        if country in high_risk_countries:
            return 0.8
        elif country in medium_risk_countries:
            return 0.5
        elif country != 'USA':
            return 0.3
        else:
            return 0.1
    
    def _calculate_merchant_risk(self, merchant_id: str) -> float:
        """Calculate risk based on merchant"""
        merchant = merchant_id.upper()
        
        high_risk = ['CRYPTO', 'CASINO', 'GAMBLING', 'CASH_ADVANCE', 'PAWN']
        medium_risk = ['MONEY_TRANSFER', 'UNKNOWN', 'TEMP', 'SHELL']
        low_risk = ['STARBUCKS', 'WALMART', 'AMAZON', 'GROCERY', 'GAS']
        
        if any(risk in merchant for risk in high_risk):
            return 0.8
        elif any(risk in merchant for risk in medium_risk):
            return 0.5
        elif any(safe in merchant for safe in low_risk):
            return 0.1
        else:
            return 0.3
    
    def _calculate_timing_risk(self, timestamp: str) -> float:
        """Calculate risk based on transaction timing"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            
            if 2 <= hour <= 5:  # Very late night
                return 0.7
            elif hour >= 23 or hour <= 1:  # Late night
                return 0.4
            elif 6 <= hour <= 22:  # Normal hours
                return 0.1
            else:
                return 0.2
        except Exception:
            return 0.3
    
    def _calculate_behavior_risk(self, history: Optional[Dict[str, Any]]) -> float:
        """Calculate risk based on customer behavior"""
        if not history:
            return 0.6  # No history is risky
        
        risk = 0.0
        
        # Account age
        account_age = history.get('account_age_days', 0)
        if account_age < 30:
            risk += 0.4
        elif account_age < 90:
            risk += 0.2
        
        # Previous declines
        declines = history.get('previous_declines', 0)
        if declines > 2:
            risk += 0.3
        elif declines > 0:
            risk += 0.1
        
        # Unusual patterns
        unusual_patterns = len(history.get('unusual_patterns', []))
        velocity_alerts = len(history.get('velocity_alerts', []))
        
        risk += min((unusual_patterns + velocity_alerts) * 0.1, 0.3)
        
        return min(risk, 1.0)
    
    def _calculate_payment_method_risk(self, payment_method: str) -> float:
        """Calculate risk based on payment method"""
        method = payment_method.upper()
        
        high_risk = ['CRYPTOCURRENCY', 'WIRE_TRANSFER', 'MONEY_ORDER', 'CASH']
        medium_risk = ['PREPAID_CARD', 'DIGITAL_WALLET']
        low_risk = ['CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER']
        
        if method in high_risk:
            return 0.7
        elif method in medium_risk:
            return 0.4
        elif method in low_risk:
            return 0.1
        else:
            return 0.3
    
    def _calculate_confidence(self, history: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence in risk assessment"""
        if not history:
            return 0.3
        
        confidence = 0.5
        
        # More transactions = higher confidence
        total_txns = history.get('total_transactions', 0)
        confidence += min(total_txns / 100, 0.3)
        
        # Account age = higher confidence
        account_age = history.get('account_age_days', 0)
        confidence += min(account_age / 365, 0.2)
        
        return min(confidence, 1.0)
    
    def _get_risk_recommendations(self, risk_level: str, score: float) -> List[str]:
        """Get recommendations based on risk level"""
        if risk_level == RiskLevel.CRITICAL.value:
            return [
                "BLOCK_TRANSACTION",
                "IMMEDIATE_MANUAL_REVIEW",
                "CONTACT_CUSTOMER",
                "FLAG_ACCOUNT"
            ]
        elif risk_level == RiskLevel.HIGH.value:
            return [
                "MANUAL_REVIEW",
                "ADDITIONAL_VERIFICATION",
                "MONITOR_ACCOUNT"
            ]
        elif risk_level == RiskLevel.MEDIUM.value:
            return [
                "ADDITIONAL_AUTHENTICATION",
                "TRANSACTION_MONITORING"
            ]
        else:
            return ["APPROVE", "ROUTINE_MONITORING"]


class ComplianceTool:
    """Tool for checking compliance rules and regulations"""
    
    async def check_compliance_rules(self, transaction: Dict[str, Any], 
                                   customer_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check transaction against compliance rules"""
        tool_logger.info(f"Checking compliance rules for transaction {transaction.get('transaction_id')}")
        
        try:
            violations = []
            warnings = []
            
            # AML checks
            aml_result = self._check_aml_rules(transaction, customer_history)
            violations.extend(aml_result['violations'])
            warnings.extend(aml_result['warnings'])
            
            # BSA/CTR checks
            bsa_result = self._check_bsa_rules(transaction, customer_history)
            violations.extend(bsa_result['violations'])
            warnings.extend(bsa_result['warnings'])
            
            # OFAC sanctions check
            ofac_result = self._check_ofac_sanctions(transaction)
            violations.extend(ofac_result['violations'])
            warnings.extend(ofac_result['warnings'])
            
            # Know Your Customer (KYC) checks
            kyc_result = self._check_kyc_requirements(transaction, customer_history)
            violations.extend(kyc_result['violations'])
            warnings.extend(kyc_result['warnings'])
            
            compliance_status = "COMPLIANT"
            if violations:
                compliance_status = "VIOLATION"
            elif warnings:
                compliance_status = "WARNING"
            
            result = {
                "transaction_id": transaction.get('transaction_id'),
                "compliance_status": compliance_status,
                "violations": violations,
                "warnings": warnings,
                "regulatory_flags": self._get_regulatory_flags(transaction),
                "required_actions": self._get_required_actions(violations, warnings),
                "reporting_requirements": self._get_reporting_requirements(transaction, violations)
            }
            
            tool_logger.info(f"Compliance check complete for {transaction.get('transaction_id')}: "
                           f"{compliance_status} ({len(violations)} violations, {len(warnings)} warnings)")
            
            return result
            
        except Exception as e:
            tool_logger.error(f"Error checking compliance rules: {e}")
            return {"error": str(e), "transaction_id": transaction.get('transaction_id')}
    
    def _check_aml_rules(self, transaction: Dict[str, Any], 
                        history: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Check Anti-Money Laundering rules"""
        violations = []
        warnings = []
        
        amount = float(transaction.get('amount', 0))
        
        # Large cash transactions
        if amount >= 10000 and transaction.get('payment_method') == 'CASH':
            violations.append("CTR_REQUIRED: Cash transaction >= $10,000")
        
        # Structuring detection — use aggregate history data since individual
        # transactions are not available in the history result
        if history and 9000 < amount < 10000:
            total_amount = history.get('total_amount', 0)
            frequency = history.get('transaction_frequency', 0)
            days_analyzed = history.get('days_analyzed', 30)
            # Estimate recent daily spend from historical averages
            estimated_daily_amount = total_amount / max(days_analyzed, 1)
            if estimated_daily_amount + amount >= 10000 and frequency >= 3:
                violations.append("STRUCTURING_SUSPECTED: Multiple transactions totaling >= $10,000")
        
        # High-risk countries
        location = transaction.get('location', {})
        high_risk_countries = ['IRN', 'PRK', 'SYR', 'AFG']
        if location.get('country') in high_risk_countries:
            warnings.append("HIGH_RISK_JURISDICTION: Transaction from sanctioned country")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_bsa_rules(self, transaction: Dict[str, Any], 
                        history: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Check Bank Secrecy Act rules"""
        violations = []
        warnings = []
        
        amount = float(transaction.get('amount', 0))
        
        # Currency Transaction Report threshold
        if amount >= 10000:
            warnings.append("CTR_THRESHOLD: Transaction meets CTR reporting requirement")
        
        # Suspicious Activity Report indicators
        merchant = transaction.get('merchant_id', '').upper()
        if 'CASH_ADVANCE' in merchant or 'MONEY_TRANSFER' in merchant:
            if amount >= 3000:
                warnings.append("SAR_INDICATOR: Large money service business transaction")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_ofac_sanctions(self, transaction: Dict[str, Any]) -> Dict[str, List[str]]:
        """Check OFAC sanctions list"""
        violations = []
        warnings = []
        
        # Simplified sanctions check (in production, use real OFAC API)
        location = transaction.get('location', {})
        sanctioned_countries = ['IRN', 'PRK', 'SYR', 'CUB', 'VEN']
        
        if location.get('country') in sanctioned_countries:
            violations.append(f"OFAC_VIOLATION: Transaction with sanctioned country {location.get('country')}")
        
        # Check merchant against simplified sanctions list
        merchant = transaction.get('merchant_name', '').upper()
        sanctioned_entities = ['SANCTIONED_BANK', 'BLOCKED_ENTITY']
        
        if any(entity in merchant for entity in sanctioned_entities):
            violations.append("OFAC_VIOLATION: Transaction with sanctioned entity")
        
        return {"violations": violations, "warnings": warnings}
    
    def _check_kyc_requirements(self, transaction: Dict[str, Any], 
                               history: Optional[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Check Know Your Customer requirements"""
        violations = []
        warnings = []
        
        amount = float(transaction.get('amount', 0))
        
        # Customer verification requirements
        if history:
            account_age = history.get('account_age_days', 0)
            if account_age < 30 and amount >= 5000:
                warnings.append("KYC_ENHANCED: New customer with large transaction")
        
        # PEP (Politically Exposed Person) checks would go here
        # For demo, randomly flag some customers
        customer_id = transaction.get('customer_id', '')
        if customer_id.endswith('999'):
            warnings.append("PEP_CHECK: Customer may be politically exposed person")
        
        return {"violations": violations, "warnings": warnings}
    
    def _get_regulatory_flags(self, transaction: Dict[str, Any]) -> List[str]:
        """Get regulatory flags for the transaction"""
        flags = []
        
        amount = float(transaction.get('amount', 0))
        if amount >= 10000:
            flags.append("BSA_REPORTING")
        
        location = transaction.get('location', {})
        if location.get('country') != 'USA':
            flags.append("INTERNATIONAL_TRANSACTION")
        
        return flags
    
    def _get_required_actions(self, violations: List[str], warnings: List[str]) -> List[str]:
        """Get required actions based on violations and warnings"""
        actions = []
        
        if violations:
            actions.append("BLOCK_TRANSACTION")
            actions.append("FILE_SAR")
            actions.append("COMPLIANCE_REVIEW")
        
        if warnings:
            actions.append("ENHANCED_MONITORING")
            if any("CTR" in warning for warning in warnings):
                actions.append("FILE_CTR")
        
        return actions
    
    def _get_reporting_requirements(self, transaction: Dict[str, Any], 
                                  violations: List[str]) -> List[str]:
        """Get reporting requirements"""
        reports = []
        
        amount = float(transaction.get('amount', 0))
        
        if amount >= 10000:
            reports.append("CTR_REPORT")
        
        if violations:
            reports.append("SAR_REPORT")
        
        if any("OFAC" in violation for violation in violations):
            reports.append("OFAC_REPORT")
        
        return reports


class AlertTool:
    """Tool for creating and managing alerts"""
    
    def __init__(self):
        self._alert_queue = None
        # Import and initialize NotificationTools for Kafka publishing
        from tools.notification import NotificationTools
        self.notification_tools = NotificationTools()

    @property
    def alert_queue(self):
        """Lazily create the asyncio.Queue inside the running event loop."""
        if self._alert_queue is None:
            self._alert_queue = asyncio.Queue()
        return self._alert_queue
    
    async def create_alert(self, transaction: Dict[str, Any], alert_type: str, 
                          severity: str, message: str, 
                          additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create an alert for suspicious activity"""
        tool_logger.info(f"Creating {severity} alert for transaction {transaction.get('transaction_id')}")
        
        try:
            alert_id = f"ALERT_{uuid.uuid4().hex[:8].upper()}"
            
            alert = {
                "alert_id": alert_id,
                "transaction_id": transaction.get('transaction_id'),
                "customer_id": transaction.get('customer_id'),
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "created_at": datetime.now().isoformat(),
                "status": "ACTIVE",
                "assigned_to": None,
                "resolution": None,
                "additional_data": additional_data or {}
            }
            
            # Add to alert queue for processing
            await self.alert_queue.put(alert)
            
            # Publish alert to Kafka via NotificationTools
            try:
                self.notification_tools.send_alert(
                    transaction_id=transaction.get('transaction_id'),
                    risk_level=severity,
                    reason=message,
                    additional_data=additional_data
                )
                tool_logger.info(f"Alert {alert_id} published to Kafka")
            except Exception as e:
                tool_logger.error(f"Failed to publish alert {alert_id} to Kafka: {e}")
            
            result = {
                "alert_id": alert_id,
                "status": "CREATED",
                "delivery_channels": self._get_delivery_channels(severity),
                "escalation_required": severity in ["HIGH", "CRITICAL"],
                "sla_hours": self._get_sla_hours(severity)
            }
            
            tool_logger.info(f"Alert {alert_id} created successfully for transaction {transaction.get('transaction_id')}")
            
            return result
            
        except Exception as e:
            tool_logger.error(f"Error creating alert: {e}")
            return {"error": str(e), "transaction_id": transaction.get('transaction_id')}
    
    def _get_delivery_channels(self, severity: str) -> List[str]:
        """Get delivery channels based on severity"""
        channels = ["EMAIL", "DASHBOARD"]
        
        if severity in ["HIGH", "CRITICAL"]:
            channels.extend(["SMS", "SLACK"])
        
        if severity == "CRITICAL":
            channels.append("PHONE")
        
        return channels
    
    def _get_sla_hours(self, severity: str) -> int:
        """Get SLA hours based on severity"""
        sla_map = {
            "LOW": 48,
            "MEDIUM": 24,
            "HIGH": 4,
            "CRITICAL": 1
        }
        return sla_map.get(severity, 24)


class TogetherAIClient:
    """Client for Together AI API with function calling"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key or "YOUR_TOGETHER_AI_API_KEY_PLACEHOLDER"
        self.base_url = "https://api.together.xyz/v1"
        self.model = os.getenv('TOGETHER_MODEL', "mistralai/Mixtral-8x7B-Instruct-v0.1")
        logger.info(f"Using AI model: {self.model}")
        self.session = None
        
        # Initialize tools
        self.history_tool = TransactionHistoryTool()
        self.risk_tool = RiskCalculatorTool()
        self.compliance_tool = ComplianceTool()
        self.alert_tool = AlertTool()
        
        # Define available functions
        self.available_functions = {
            "check_transaction_history": {
                "function": self.history_tool.check_transaction_history,
                "description": "Check customer's transaction history and behavior patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {
                            "type": "string",
                            "description": "Customer ID to analyze"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Number of days to look back (default: 30)"
                        }
                    },
                    "required": ["customer_id"]
                }
            },
            "calculate_risk_score": {
                "function": self.risk_tool.calculate_risk_score,
                "description": "Calculate comprehensive risk score for the transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction data to analyze"
                        },
                        "customer_history": {
                            "type": "object",
                            "description": "Customer history data from previous tool call"
                        }
                    },
                    "required": ["transaction"]
                }
            },
            "check_compliance_rules": {
                "function": self.compliance_tool.check_compliance_rules,
                "description": "Check transaction against compliance and regulatory rules",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction data to check"
                        },
                        "customer_history": {
                            "type": "object",
                            "description": "Customer history data from previous tool call"
                        }
                    },
                    "required": ["transaction"]
                }
            },
            "create_alert": {
                "function": self.alert_tool.create_alert,
                "description": "Create an alert for suspicious or non-compliant transactions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction data"
                        },
                        "alert_type": {
                            "type": "string",
                            "description": "Type of alert (FRAUD, COMPLIANCE, AML, etc.)"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Alert severity (LOW, MEDIUM, HIGH, CRITICAL)"
                        },
                        "message": {
                            "type": "string",
                            "description": "Alert message describing the issue"
                        },
                        "additional_data": {
                            "type": "object",
                            "description": "Additional data for the alert"
                        }
                    },
                    "required": ["transaction", "alert_type", "severity", "message"]
                }
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _format_tools_for_api(self) -> List[Dict[str, Any]]:
        """Format tools for API call"""
        tools = []
        for name, func_info in self.available_functions.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": func_info["description"],
                    "parameters": func_info["parameters"]
                }
            })
        return tools
    
    async def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction using AI with function calling"""
        transaction_id = transaction.get('transaction_id', 'unknown')
        
        api_logger.info(f"Starting AI analysis for transaction {transaction_id}")
        
        start_time = time.time()
        tool_calls_made = []
        tool_results = {}
        reasoning_steps = []
        
        try:
            # System prompt for fraud detection
            system_prompt = """You are an expert financial fraud detection analyst. Your job is to analyze transactions and determine if they should be approved, declined, require manual review, or need additional authentication.

You have access to several tools:
1. check_transaction_history - Get customer's historical transaction patterns
2. calculate_risk_score - Calculate comprehensive risk assessment  
3. check_compliance_rules - Verify regulatory compliance
4. create_alert - Create alerts for suspicious activity

ANALYSIS PROCESS:
1. First, check the customer's transaction history to understand their normal patterns
2. Calculate a comprehensive risk score based on the transaction and history
3. Check compliance rules to ensure regulatory requirements are met
4. If any red flags are found, create appropriate alerts
5. Make a final decision based on all the information

DECISION CRITERIA:
- APPROVE: Low risk, compliant, matches customer patterns
- DECLINE: High/critical risk, compliance violations, clear fraud indicators
- MANUAL_REVIEW: Medium-high risk, unusual patterns requiring human review
- ADDITIONAL_AUTH: Medium risk, could be legitimate but needs verification

IMPORTANT: After your analysis, you MUST include exactly one of the following decision tokens on its own line in your final response:
DECISION: APPROVE
DECISION: DECLINE
DECISION: MANUAL_REVIEW
DECISION: ADDITIONAL_AUTH

Be thorough but efficient. Use your tools strategically and provide clear reasoning for your decision."""

            user_message = f"""Analyze this financial transaction:

Transaction Details:
{json.dumps(transaction, indent=2)}

Please use your available tools to conduct a thorough analysis and provide a decision with clear reasoning."""

            # Make API call with function calling
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            # Multi-turn tool-call loop: call API → execute tools → send results back → repeat
            max_iterations = 5
            last_response_id = ''
            total_tokens = 0

            for iteration in range(max_iterations):
                payload = {
                    "model": self.model,
                    "messages": messages,
                    "tools": self._format_tools_for_api(),
                    "tool_choice": "auto",
                    "max_tokens": 4000,
                    "temperature": 0.1
                }

                api_logger.debug(f"Making API call for transaction {transaction_id} (iteration {iteration + 1})")

                async with self.session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        api_logger.error(f"API error {response.status}: {error_text}")
                        raise Exception(f"API error {response.status}: {error_text}")

                    result = await response.json()
                    last_response_id = result.get('id', '')
                    total_tokens += result.get('usage', {}).get('total_tokens', 0)

                message = result['choices'][0]['message']
                pending_tool_calls = message.get('tool_calls')

                if not pending_tool_calls:
                    # No more tool calls — model returned a final text response
                    break

                # Append the assistant message (with tool_calls) to conversation
                messages.append(message)

                reasoning_logger.info(f"AI requested {len(pending_tool_calls)} tool calls (iteration {iteration + 1})")

                # Execute each tool call and append results as tool messages
                for tool_call in pending_tool_calls:
                    function_name = tool_call['function']['name']
                    arguments = json.loads(tool_call['function']['arguments'])
                    tool_call_id = tool_call.get('id', '')

                    reasoning_logger.info(f"Executing tool: {function_name} with args: {arguments}")
                    tool_calls_made.append(function_name)

                    if function_name in self.available_functions:
                        try:
                            func = self.available_functions[function_name]['function']
                            tool_result = await func(**arguments)
                            tool_results[function_name] = tool_result
                            reasoning_steps.append(f"Executed {function_name}: {tool_result}")
                        except Exception as e:
                            error_msg = f"Tool execution error for {function_name}: {str(e)}"
                            reasoning_logger.error(error_msg)
                            tool_result = {"error": str(e)}
                            tool_results[function_name] = tool_result
                            reasoning_steps.append(error_msg)
                    else:
                        tool_result = {"error": f"Unknown function: {function_name}"}
                        tool_results[function_name] = tool_result

                    # Append the tool result message for the model
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": json.dumps(tool_result, default=str)
                    })

            # Extract decision from the final AI response
            ai_reasoning = message.get('content', '') or ''
            reasoning_steps.append(f"AI Reasoning: {ai_reasoning}")

            decision_type = self._extract_decision_type(ai_reasoning, tool_results)
            risk_level = self._extract_risk_level(tool_results)
            confidence_score = self._extract_confidence_score(tool_results)

            reasoning_logger.info(f"Final decision: {decision_type} (risk: {risk_level}, confidence: {confidence_score})")

            processing_time = int((time.time() - start_time) * 1000)

            # Create final decision object
            decision = AIDecision(
                decision_id=f"DEC_{uuid.uuid4().hex[:8].upper()}",
                transaction_id=transaction_id,
                customer_id=transaction.get('customer_id', ''),
                decision_type=decision_type,
                risk_level=risk_level,
                confidence_score=confidence_score,
                reasoning=ai_reasoning,
                tool_calls_made=tool_calls_made,
                tool_results=tool_results,
                processing_time_ms=processing_time,
                model_used=self.model,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "reasoning_steps": reasoning_steps,
                    "api_response_id": last_response_id,
                    "total_tokens": total_tokens
                }
            )

            api_logger.info(f"AI analysis complete for {transaction_id}: "
                          f"{decision_type} ({processing_time}ms)")

            return asdict(decision)
                
        except Exception as e:
            api_logger.error(f"Error in AI analysis for {transaction_id}: {e}")
            traceback.print_exc()
            
            # Return error decision
            return asdict(AIDecision(
                decision_id=f"DEC_{uuid.uuid4().hex[:8].upper()}",
                transaction_id=transaction_id,
                customer_id=transaction.get('customer_id', ''),
                decision_type=DecisionType.MANUAL_REVIEW.value,
                risk_level=RiskLevel.HIGH.value,
                confidence_score=0.0,
                reasoning=f"Error during analysis: {str(e)}",
                tool_calls_made=[],
                tool_results={"error": str(e)},
                processing_time_ms=int((time.time() - start_time) * 1000),
                model_used=self.model,
                timestamp=datetime.now().isoformat(),
                metadata={"error": True}
            ))
    
    _VALID_DECISIONS = {dt.value for dt in DecisionType}

    def _extract_decision_type(self, ai_reasoning: str, tool_results: Dict[str, Any]) -> str:
        """Extract decision type from AI reasoning and tool results"""
        import re

        # 1. Look for structured decision token: "DECISION: <TYPE>"
        match = re.search(r'DECISION:\s*(APPROVE|DECLINE|MANUAL_REVIEW|ADDITIONAL_AUTH)', ai_reasoning, re.IGNORECASE)
        if match:
            token = match.group(1).upper()
            if token in self._VALID_DECISIONS:
                return token

        # 2. Fall back to tool-result-based heuristics
        risk_result = tool_results.get('calculate_risk_score', {})
        compliance_result = tool_results.get('check_compliance_rules', {})

        if risk_result.get('risk_level') == 'CRITICAL':
            return DecisionType.DECLINE.value

        if compliance_result.get('compliance_status') == 'VIOLATION':
            return DecisionType.DECLINE.value

        if risk_result.get('risk_level') == 'HIGH':
            return DecisionType.MANUAL_REVIEW.value

        if risk_result.get('risk_level') == 'MEDIUM':
            return DecisionType.ADDITIONAL_AUTH.value

        # Default to approve for low risk
        return DecisionType.APPROVE.value
    
    def _extract_risk_level(self, tool_results: Dict[str, Any]) -> str:
        """Extract risk level from tool results"""
        risk_result = tool_results.get('calculate_risk_score', {})
        return risk_result.get('risk_level', RiskLevel.MEDIUM.value)
    
    def _extract_confidence_score(self, tool_results: Dict[str, Any]) -> float:
        """Extract confidence score from tool results"""
        risk_result = tool_results.get('calculate_risk_score', {})
        return risk_result.get('confidence', 0.5)


class TransactionProcessor:
    """Main processor for handling transactions"""
    
    @staticmethod
    def _build_kafka_base_config(config: Dict[str, str]) -> Dict[str, Any]:
        """Build shared Kafka config keys used by both consumer and producer."""
        return {
            'bootstrap.servers': config['bootstrap.servers'],
            'security.protocol': config.get('security.protocol', 'SASL_SSL'),
            'sasl.mechanism': config.get('sasl.mechanism', 'PLAIN'),
            'sasl.username': config.get('sasl.username'),
            'sasl.password': config.get('sasl.password'),
            'ssl.endpoint.identification.algorithm': config.get('ssl.endpoint.identification.algorithm', 'https'),
            'request.timeout.ms': config.get('request.timeout.ms', 40000),
            'retry.backoff.ms': config.get('retry.backoff.ms', 1000),
        }

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.running = False

        base_config = self._build_kafka_base_config(config)

        # Setup Kafka consumer
        consumer_config = {
            **base_config,
            'group.id': config.get('group.id', 'ai-processor-group'),
            'auto.offset.reset': 'latest',
            'enable.auto.commit': False,
            'session.timeout.ms': config.get('session.timeout.ms', 30000),
        }

        # Setup Kafka producer for decisions
        producer_config = {
            **base_config,
            'client.id': 'ai-decision-producer',
        }

        self.consumer = Consumer(consumer_config)
        self.producer = Producer(producer_config)
        
        self.input_topic = config.get('input_topic', 'financial-transactions')
        self.output_topic = config.get('output_topic', 'ai-decisions')
        
        # Statistics
        self.processed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start_processing(self):
        """Start the main processing loop"""
        logger.info("Starting AI transaction processor...")
        
        self.running = True
        self.consumer.subscribe([self.input_topic])
        
        # Initialize Together AI client
        async with TogetherAIClient(self.config.get('together_api_key')) as ai_client:
            
            try:
                while self.running:
                    # Poll for messages
                    msg = self.consumer.poll(timeout=1.0)
                    
                    if msg is None:
                        continue
                    
                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            continue
                        else:
                            logger.error(f"Consumer error: {msg.error()}")
                            continue
                    
                    # Process the transaction
                    await self._process_transaction(msg, ai_client)
                    
                    # Commit the offset
                    self.consumer.commit(msg)
                    
                    # Log progress
                    if self.processed_count % 10 == 0:
                        self._log_statistics()
                        
            except Exception as e:
                logger.error(f"Processing error: {e}")
                traceback.print_exc()
            finally:
                await self._shutdown()
    
    async def _process_transaction(self, msg, ai_client):
        """Process a single transaction"""
        try:
            # Parse transaction
            transaction = json.loads(msg.value().decode('utf-8'))
            transaction_id = transaction.get('transaction_id', 'unknown')
            
            logger.info(f"Processing transaction {transaction_id}")
            
            # Analyze with AI
            decision = await ai_client.analyze_transaction(transaction)
            
            # Send decision to output topic
            await self._send_decision(decision)
            
            self.processed_count += 1
            
            logger.info(f"Completed processing transaction {transaction_id}: "
                       f"{decision['decision_type']} ({decision['processing_time_ms']}ms)")
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing transaction: {e}")
            traceback.print_exc()
    
    async def _send_decision(self, decision: Dict[str, Any]):
        """Send decision to output topic"""
        try:
            decision_json = json.dumps(decision, default=str)
            
            self.producer.produce(
                topic=self.output_topic,
                key=decision['transaction_id'],
                value=decision_json,
                callback=self._delivery_callback
            )
            
            # Poll for delivery reports
            self.producer.poll(0)
            
        except Exception as e:
            logger.error(f"Error sending decision: {e}")
    
    def _delivery_callback(self, err, msg):
        """Callback for message delivery"""
        if err:
            logger.error(f"Decision delivery failed: {err}")
        else:
            logger.debug(f"Decision delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")
    
    def _log_statistics(self):
        """Log processing statistics"""
        uptime = time.time() - self.start_time
        rate = self.processed_count / uptime if uptime > 0 else 0
        
        logger.info(f"Statistics: Processed={self.processed_count}, "
                   f"Errors={self.error_count}, "
                   f"Rate={rate:.2f} tx/sec, "
                   f"Uptime={uptime:.0f}s")
    
    async def _shutdown(self):
        """Shutdown the processor"""
        logger.info("Shutting down processor...")
        
        # Close consumer
        self.consumer.close()
        
        # Flush producer
        remaining = self.producer.flush(30)
        if remaining > 0:
            logger.warning(f"{remaining} messages were not delivered")
        
        self._log_statistics()
        logger.info("Processor shutdown complete")


def load_config() -> Dict[str, str]:
    """Load configuration from environment"""
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
        'security.protocol': os.getenv('CONFLUENT_SECURITY_PROTOCOL', 'SASL_SSL'),
        'sasl.mechanism': os.getenv('CONFLUENT_SASL_MECHANISM', 'PLAIN'),
        'sasl.username': os.getenv('CONFLUENT_API_KEY'),
        'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
        'ssl.endpoint.identification.algorithm': os.getenv('CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM', 'https'),
        'group.id': os.getenv('KAFKA_GROUP_ID', 'ai-processor-group'),
        'input_topic': os.getenv('KAFKA_TOPIC_TRANSACTIONS', 'financial-transactions'),
        'output_topic': os.getenv('KAFKA_TOPIC_DECISIONS', 'ai-decisions'),
        'together_api_key': os.getenv('TOGETHER_API_KEY'),
        'session.timeout.ms': int(os.getenv('KAFKA_SESSION_TIMEOUT_MS', '30000')),
        'request.timeout.ms': int(os.getenv('KAFKA_REQUEST_TIMEOUT_MS', '40000')),
        'retry.backoff.ms': int(os.getenv('KAFKA_RETRY_BACKOFF_MS', '1000'))
    }
    
    # Validate required Confluent Cloud configuration
    required_keys = ['bootstrap.servers', 'sasl.username', 'sasl.password', 'together_api_key']
    for key in required_keys:
        if not config.get(key):
            logger.error(f"Missing required configuration: {key}")
            if key in ['bootstrap.servers', 'sasl.username', 'sasl.password']:
                logger.error("Please ensure CONFLUENT_BOOTSTRAP_SERVERS, CONFLUENT_API_KEY, and CONFLUENT_API_SECRET are set")
            elif key == 'together_api_key':
                logger.error("Please ensure TOGETHER_API_KEY is set")
            raise ValueError(f"Missing required configuration: {key}")
    
    return config


async def main():
    """Main function"""
    config = load_config()
    
    processor = TransactionProcessor(config)
    await processor.start_processing()


if __name__ == "__main__":
    asyncio.run(main())