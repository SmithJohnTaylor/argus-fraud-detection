#!/usr/bin/env python3
"""
Financial Transaction Analysis Tools
Implements core business logic for fraud detection and compliance checking
"""

import json
import logging
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

# Configure logging
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    MINIMAL = "MINIMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertPriority(Enum):
    P1_CRITICAL = "P1_CRITICAL"  # 1 hour SLA
    P2_HIGH = "P2_HIGH"         # 4 hour SLA
    P3_MEDIUM = "P3_MEDIUM"     # 24 hour SLA
    P4_LOW = "P4_LOW"           # 48 hour SLA


@dataclass
class CustomerProfile:
    customer_id: str
    account_age_days: int
    verification_status: str
    account_type: str
    credit_score: Optional[int]
    employment_verified: bool
    phone_verified: bool
    email_verified: bool
    identity_verified: bool
    risk_tier: str
    monthly_income: Optional[float]
    debt_to_income_ratio: Optional[float]


@dataclass
class TransactionHistory:
    customer_id: str
    lookback_days: int
    total_transactions: int
    total_amount: float
    average_amount: float
    median_amount: float
    max_amount: float
    min_amount: float
    transaction_frequency_per_day: float
    unique_merchants: int
    unique_locations: int
    common_merchants: List[str]
    common_locations: List[str]
    common_transaction_hours: List[int]
    weekend_transaction_ratio: float
    international_transaction_ratio: float
    declined_transactions: int
    declined_amount: float
    velocity_patterns: Dict[str, Any]
    spending_categories: Dict[str, float]
    risk_indicators: List[str]


@dataclass
class RiskAssessment:
    transaction_id: str
    overall_risk_score: float
    risk_level: str
    confidence_score: float
    risk_factors: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    next_actions: List[str]


@dataclass
class ComplianceCheck:
    transaction_id: str
    overall_status: str
    aml_status: str
    kyc_status: str
    sanctions_status: str
    pep_status: str
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    required_reports: List[str]
    regulatory_flags: List[str]
    investigation_required: bool


@dataclass
class Alert:
    alert_id: str
    transaction_id: str
    customer_id: str
    alert_type: str
    priority: str
    severity: str
    title: str
    description: str
    reasoning: str
    recommended_actions: List[str]
    assigned_team: str
    sla_hours: int
    escalation_required: bool
    created_at: str
    metadata: Dict[str, Any]


class TransactionHistoryTool:
    """Tool for retrieving and analyzing customer transaction history"""
    
    def __init__(self):
        # Mock database of customer profiles
        self.customer_profiles: Dict[str, CustomerProfile] = {}
        # Mock transaction history cache
        self.transaction_cache: Dict[str, List[Dict[str, Any]]] = {}
        
        # Merchant categories for realistic data generation
        self.merchant_categories = {
            'grocery': ['WHOLE_FOODS', 'KROGER', 'SAFEWAY', 'WALMART_GROCERY', 'TRADER_JOES'],
            'restaurant': ['MCDONALDS', 'STARBUCKS', 'SUBWAY', 'CHIPOTLE', 'PANERA'],
            'gas': ['SHELL', 'EXXON', 'CHEVRON', 'BP', 'MOBIL'],
            'retail': ['AMAZON', 'TARGET', 'WALMART', 'BEST_BUY', 'MACYS'],
            'entertainment': ['NETFLIX', 'SPOTIFY', 'CINEMA', 'THEATER', 'GAMING'],
            'travel': ['UBER', 'AIRBNB', 'HOTEL', 'AIRLINE', 'RENTAL_CAR'],
            'financial': ['BANK_TRANSFER', 'ATM_WITHDRAWAL', 'LOAN_PAYMENT', 'INVESTMENT'],
            'healthcare': ['PHARMACY', 'HOSPITAL', 'DOCTOR', 'DENTAL', 'INSURANCE'],
            'utilities': ['ELECTRIC_BILL', 'WATER_BILL', 'INTERNET', 'PHONE_BILL', 'GAS_BILL'],
            'high_risk': ['CRYPTO_EXCHANGE', 'CASINO', 'MONEY_TRANSFER', 'PAWN_SHOP', 'CASH_ADVANCE']
        }
        
        # Location data for realistic patterns
        self.locations = {
            'domestic_common': [
                'New York, NY, USA', 'Los Angeles, CA, USA', 'Chicago, IL, USA',
                'Houston, TX, USA', 'Phoenix, AZ, USA', 'Philadelphia, PA, USA'
            ],
            'domestic_medium': [
                'Las Vegas, NV, USA', 'Miami, FL, USA', 'Seattle, WA, USA',
                'Denver, CO, USA', 'Atlanta, GA, USA', 'Boston, MA, USA'
            ],
            'international_safe': [
                'London, UK', 'Toronto, Canada', 'Paris, France',
                'Tokyo, Japan', 'Sydney, Australia', 'Amsterdam, Netherlands'
            ],
            'international_risky': [
                'Lagos, Nigeria', 'Bucharest, Romania', 'Kiev, Ukraine',
                'Bangkok, Thailand', 'Manila, Philippines', 'Unknown Location'
            ]
        }
    
    def check_transaction_history(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """
        Retrieve and analyze customer transaction history
        
        Args:
            customer_id: Customer identifier
            days: Number of days to look back
            
        Returns:
            Structured transaction history analysis
        """
        logger.info(f"Checking transaction history for customer {customer_id} ({days} days)")
        
        try:
            # Get or create customer profile
            profile = self._get_customer_profile(customer_id)
            
            # Generate or retrieve transaction history
            transactions = self._get_transaction_history(customer_id, days)
            
            # Analyze the transaction data
            analysis = self._analyze_transaction_patterns(transactions, profile, days)
            
            # Create structured response
            history = TransactionHistory(
                customer_id=customer_id,
                lookback_days=days,
                total_transactions=analysis['total_transactions'],
                total_amount=analysis['total_amount'],
                average_amount=analysis['average_amount'],
                median_amount=analysis['median_amount'],
                max_amount=analysis['max_amount'],
                min_amount=analysis['min_amount'],
                transaction_frequency_per_day=analysis['frequency_per_day'],
                unique_merchants=analysis['unique_merchants'],
                unique_locations=analysis['unique_locations'],
                common_merchants=analysis['common_merchants'],
                common_locations=analysis['common_locations'],
                common_transaction_hours=analysis['common_hours'],
                weekend_transaction_ratio=analysis['weekend_ratio'],
                international_transaction_ratio=analysis['international_ratio'],
                declined_transactions=analysis['declined_count'],
                declined_amount=analysis['declined_amount'],
                velocity_patterns=analysis['velocity_patterns'],
                spending_categories=analysis['spending_categories'],
                risk_indicators=analysis['risk_indicators']
            )
            
            result = {
                "status": "success",
                "customer_profile": asdict(profile),
                "transaction_history": asdict(history),
                "analysis_metadata": {
                    "analysis_date": datetime.now().isoformat(),
                    "data_completeness": analysis['data_completeness'],
                    "confidence_level": analysis['confidence_level']
                }
            }
            
            logger.info(f"Transaction history analysis complete for {customer_id}: "
                       f"{analysis['total_transactions']} transactions, "
                       f"${analysis['total_amount']:.2f} total volume")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking transaction history for {customer_id}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "customer_id": customer_id
            }
    
    def _get_customer_profile(self, customer_id: str) -> CustomerProfile:
        """Get or create a realistic customer profile"""
        if customer_id not in self.customer_profiles:
            # Generate deterministic but varied profile based on customer_id
            seed = int(hashlib.md5(customer_id.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            
            # Account age distribution
            account_age_weights = [0.1, 0.2, 0.3, 0.25, 0.15]  # 0-30, 31-90, 91-365, 366-1095, 1096+ days
            age_ranges = [(1, 30), (31, 90), (91, 365), (366, 1095), (1096, 3650)]
            age_range = random.choices(age_ranges, weights=account_age_weights)[0]
            account_age = random.randint(age_range[0], age_range[1])
            
            # Verification status based on account age
            verification_rate = min(0.5 + (account_age / 365) * 0.4, 0.95)
            
            # Risk tier distribution
            risk_tiers = ['LOW', 'MEDIUM', 'HIGH']
            risk_weights = [0.7, 0.25, 0.05]
            risk_tier = random.choices(risk_tiers, weights=risk_weights)[0]
            
            profile = CustomerProfile(
                customer_id=customer_id,
                account_age_days=account_age,
                verification_status="VERIFIED" if random.random() < verification_rate else "PARTIAL",
                account_type=random.choices(['CHECKING', 'SAVINGS', 'PREMIUM'], weights=[0.6, 0.3, 0.1])[0],
                credit_score=random.randint(550, 850) if random.random() < 0.8 else None,
                employment_verified=random.random() < verification_rate,
                phone_verified=random.random() < (verification_rate + 0.1),
                email_verified=random.random() < (verification_rate + 0.15),
                identity_verified=random.random() < verification_rate,
                risk_tier=risk_tier,
                monthly_income=random.uniform(3000, 15000) if random.random() < 0.7 else None,
                debt_to_income_ratio=random.uniform(0.1, 0.6) if random.random() < 0.6 else None
            )
            
            self.customer_profiles[customer_id] = profile
            
            # Reset random seed
            random.seed()
        
        return self.customer_profiles[customer_id]
    
    def _get_transaction_history(self, customer_id: str, days: int) -> List[Dict[str, Any]]:
        """Generate realistic transaction history"""
        if customer_id not in self.transaction_cache:
            profile = self.customer_profiles[customer_id]
            
            # Generate deterministic transactions
            seed = int(hashlib.md5(f"{customer_id}_txns".encode()).hexdigest()[:8], 16)
            random.seed(seed)
            
            transactions = []
            
            # Base transaction frequency based on account type and age
            base_frequency = {
                'CHECKING': 2.5,
                'SAVINGS': 0.8,
                'PREMIUM': 4.2
            }.get(profile.account_type, 2.0)
            
            # Adjust frequency based on account age (newer accounts less active)
            age_factor = min(profile.account_age_days / 180, 1.0)
            daily_frequency = base_frequency * age_factor
            
            # Generate transactions for the period
            start_date = datetime.now() - timedelta(days=days)
            
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Weekend effect (less activity)
                weekend_factor = 0.6 if current_date.weekday() >= 5 else 1.0
                
                # Number of transactions for this day
                day_frequency = daily_frequency * weekend_factor
                num_transactions = random.poisson(day_frequency)
                
                for _ in range(num_transactions):
                    transaction = self._generate_single_transaction(current_date, profile)
                    transactions.append(transaction)
            
            self.transaction_cache[customer_id] = transactions
            random.seed()  # Reset seed
        
        return self.transaction_cache[customer_id]
    
    def _generate_single_transaction(self, date: datetime, profile: CustomerProfile) -> Dict[str, Any]:
        """Generate a single realistic transaction"""
        
        # Select merchant category based on profile and randomness
        category_weights = {
            'grocery': 0.25,
            'restaurant': 0.20,
            'gas': 0.10,
            'retail': 0.15,
            'entertainment': 0.08,
            'travel': 0.05,
            'financial': 0.07,
            'healthcare': 0.04,
            'utilities': 0.05,
            'high_risk': 0.01 if profile.risk_tier == 'LOW' else 0.03
        }
        
        category = random.choices(list(category_weights.keys()), 
                                weights=list(category_weights.values()))[0]
        merchant = random.choice(self.merchant_categories[category])
        
        # Amount based on category and customer profile
        amount_ranges = {
            'grocery': (15, 200),
            'restaurant': (8, 150),
            'gas': (25, 100),
            'retail': (20, 800),
            'entertainment': (10, 100),
            'travel': (50, 2000),
            'financial': (100, 5000),
            'healthcare': (25, 500),
            'utilities': (50, 300),
            'high_risk': (100, 10000)
        }
        
        min_amt, max_amt = amount_ranges[category]
        
        # Adjust for customer income if available
        if profile.monthly_income:
            income_factor = profile.monthly_income / 6000  # Normalize around $6k
            max_amt *= income_factor
        
        amount = round(random.uniform(min_amt, max_amt), 2)
        
        # Transaction time (business hours more likely)
        if random.random() < 0.8:  # Normal hours
            hour = random.choices(range(24), weights=[
                1, 1, 1, 1, 1, 2, 4, 6, 8, 10, 10, 10,  # 0-11
                10, 10, 8, 8, 8, 10, 12, 10, 8, 6, 4, 2   # 12-23
            ])[0]
        else:  # Unusual hours
            hour = random.choice([0, 1, 2, 3, 4, 5, 23])
        
        timestamp = date.replace(
            hour=hour,
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        
        # Location based on risk profile
        if category == 'high_risk' or random.random() < 0.05:
            location_type = random.choice(['international_risky', 'domestic_medium'])
        elif random.random() < 0.15:
            location_type = 'international_safe'
        else:
            location_type = 'domestic_common'
        
        location = random.choice(self.locations[location_type])
        
        # Payment method
        payment_methods = ['CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'DIGITAL_WALLET']
        if category == 'high_risk':
            payment_methods.extend(['WIRE_TRANSFER', 'CASH', 'CRYPTOCURRENCY'])
        
        payment_method = random.choice(payment_methods)
        
        # Transaction status (most approved)
        status_weights = [0.92, 0.05, 0.03]  # APPROVED, DECLINED, PENDING
        status = random.choices(['APPROVED', 'DECLINED', 'PENDING'], weights=status_weights)[0]
        
        return {
            'transaction_id': f"TXN_{uuid.uuid4().hex[:8].upper()}",
            'timestamp': timestamp.isoformat(),
            'amount': amount,
            'merchant': merchant,
            'merchant_category': category,
            'location': location,
            'payment_method': payment_method,
            'status': status,
            'hour': hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5,
            'is_international': 'USA' not in location
        }
    
    def _analyze_transaction_patterns(self, transactions: List[Dict[str, Any]], 
                                   profile: CustomerProfile, days: int) -> Dict[str, Any]:
        """Analyze transaction patterns for insights"""
        
        if not transactions:
            return self._empty_analysis(days)
        
        # Basic statistics
        amounts = [tx['amount'] for tx in transactions if tx['status'] == 'APPROVED']
        total_transactions = len(transactions)
        approved_transactions = len(amounts)
        declined_transactions = len([tx for tx in transactions if tx['status'] == 'DECLINED'])
        
        total_amount = sum(amounts) if amounts else 0
        average_amount = total_amount / len(amounts) if amounts else 0
        median_amount = sorted(amounts)[len(amounts)//2] if amounts else 0
        max_amount = max(amounts) if amounts else 0
        min_amount = min(amounts) if amounts else 0
        
        # Frequency analysis
        frequency_per_day = total_transactions / days if days > 0 else 0
        
        # Merchant and location analysis
        merchants = [tx['merchant'] for tx in transactions]
        locations = [tx['location'] for tx in transactions]
        unique_merchants = len(set(merchants))
        unique_locations = len(set(locations))
        
        # Get most common merchants and locations
        from collections import Counter
        merchant_counts = Counter(merchants)
        location_counts = Counter(locations)
        common_merchants = [item[0] for item in merchant_counts.most_common(5)]
        common_locations = [item[0] for item in location_counts.most_common(3)]
        
        # Time analysis
        hours = [tx['hour'] for tx in transactions]
        common_hours = [item[0] for item in Counter(hours).most_common(3)]
        
        weekend_transactions = len([tx for tx in transactions if tx['is_weekend']])
        weekend_ratio = weekend_transactions / total_transactions if total_transactions > 0 else 0
        
        international_transactions = len([tx for tx in transactions if tx['is_international']])
        international_ratio = international_transactions / total_transactions if total_transactions > 0 else 0
        
        # Declined transaction analysis
        declined_amount = sum([tx['amount'] for tx in transactions if tx['status'] == 'DECLINED'])
        
        # Spending categories
        category_spending = {}
        for tx in transactions:
            if tx['status'] == 'APPROVED':
                category = tx['merchant_category']
                category_spending[category] = category_spending.get(category, 0) + tx['amount']
        
        # Velocity analysis
        velocity_patterns = self._analyze_velocity_patterns(transactions)
        
        # Risk indicators
        risk_indicators = self._identify_risk_indicators(transactions, profile)
        
        # Data quality metrics
        data_completeness = min(1.0, len(transactions) / (days * 2))  # Expect ~2 transactions per day
        confidence_level = min(0.9, 0.3 + (len(transactions) / 100) * 0.6)  # Higher confidence with more data
        
        return {
            'total_transactions': total_transactions,
            'total_amount': round(total_amount, 2),
            'average_amount': round(average_amount, 2),
            'median_amount': round(median_amount, 2),
            'max_amount': round(max_amount, 2),
            'min_amount': round(min_amount, 2),
            'frequency_per_day': round(frequency_per_day, 2),
            'unique_merchants': unique_merchants,
            'unique_locations': unique_locations,
            'common_merchants': common_merchants,
            'common_locations': common_locations,
            'common_hours': common_hours,
            'weekend_ratio': round(weekend_ratio, 3),
            'international_ratio': round(international_ratio, 3),
            'declined_count': declined_transactions,
            'declined_amount': round(declined_amount, 2),
            'velocity_patterns': velocity_patterns,
            'spending_categories': {k: round(v, 2) for k, v in category_spending.items()},
            'risk_indicators': risk_indicators,
            'data_completeness': round(data_completeness, 3),
            'confidence_level': round(confidence_level, 3)
        }
    
    def _analyze_velocity_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transaction velocity patterns"""
        
        # Sort transactions by timestamp
        sorted_txns = sorted(transactions, key=lambda x: x['timestamp'])
        
        # Analyze hourly, daily patterns
        hourly_velocity = {}
        daily_velocity = {}
        
        for tx in sorted_txns:
            timestamp = datetime.fromisoformat(tx['timestamp'])
            hour_key = timestamp.strftime('%Y-%m-%d %H:00')
            day_key = timestamp.strftime('%Y-%m-%d')
            
            hourly_velocity[hour_key] = hourly_velocity.get(hour_key, 0) + 1
            daily_velocity[day_key] = daily_velocity.get(day_key, 0) + 1
        
        # Find velocity spikes
        max_hourly = max(hourly_velocity.values()) if hourly_velocity else 0
        max_daily = max(daily_velocity.values()) if daily_velocity else 0
        avg_daily = sum(daily_velocity.values()) / len(daily_velocity) if daily_velocity else 0
        
        velocity_alerts = []
        if max_hourly >= 5:
            velocity_alerts.append(f"High hourly velocity: {max_hourly} transactions in one hour")
        if max_daily > avg_daily * 3:
            velocity_alerts.append(f"High daily velocity: {max_daily} transactions in one day")
        
        return {
            'max_transactions_per_hour': max_hourly,
            'max_transactions_per_day': max_daily,
            'average_transactions_per_day': round(avg_daily, 2),
            'velocity_alerts': velocity_alerts
        }
    
    def _identify_risk_indicators(self, transactions: List[Dict[str, Any]], 
                                profile: CustomerProfile) -> List[str]:
        """Identify risk indicators from transaction patterns"""
        
        indicators = []
        
        # High-risk merchant usage
        high_risk_count = len([tx for tx in transactions if tx['merchant_category'] == 'high_risk'])
        if high_risk_count > 0:
            indicators.append(f"High-risk merchant usage: {high_risk_count} transactions")
        
        # Unusual time patterns
        late_night_count = len([tx for tx in transactions if tx['hour'] in [0, 1, 2, 3, 4]])
        if late_night_count > len(transactions) * 0.1:
            indicators.append(f"Frequent late-night activity: {late_night_count} transactions")
        
        # International activity
        international_count = len([tx for tx in transactions if tx['is_international']])
        if international_count > len(transactions) * 0.2:
            indicators.append(f"High international activity: {international_count} transactions")
        
        # Large transaction spikes
        amounts = [tx['amount'] for tx in transactions if tx['status'] == 'APPROVED']
        if amounts:
            avg_amount = sum(amounts) / len(amounts)
            large_transactions = [amt for amt in amounts if amt > avg_amount * 5]
            if large_transactions:
                indicators.append(f"Large transaction spikes: {len(large_transactions)} transactions")
        
        # High decline rate
        total_count = len(transactions)
        declined_count = len([tx for tx in transactions if tx['status'] == 'DECLINED'])
        if total_count > 0 and declined_count / total_count > 0.1:
            indicators.append(f"High decline rate: {declined_count}/{total_count} transactions")
        
        # New account with high activity
        if profile.account_age_days < 30 and len(transactions) > 50:
            indicators.append("New account with unusually high activity")
        
        return indicators
    
    def _empty_analysis(self, days: int) -> Dict[str, Any]:
        """Return empty analysis structure"""
        return {
            'total_transactions': 0,
            'total_amount': 0.0,
            'average_amount': 0.0,
            'median_amount': 0.0,
            'max_amount': 0.0,
            'min_amount': 0.0,
            'frequency_per_day': 0.0,
            'unique_merchants': 0,
            'unique_locations': 0,
            'common_merchants': [],
            'common_locations': [],
            'common_hours': [],
            'weekend_ratio': 0.0,
            'international_ratio': 0.0,
            'declined_count': 0,
            'declined_amount': 0.0,
            'velocity_patterns': {'max_transactions_per_hour': 0, 'max_transactions_per_day': 0, 
                                'average_transactions_per_day': 0.0, 'velocity_alerts': []},
            'spending_categories': {},
            'risk_indicators': ["No transaction history available"],
            'data_completeness': 0.0,
            'confidence_level': 0.0
        }


class RiskCalculatorTool:
    """Tool for calculating comprehensive risk scores"""
    
    def __init__(self):
        # Risk scoring weights for different factors
        self.risk_weights = {
            'amount_risk': 0.25,
            'merchant_risk': 0.20,
            'location_risk': 0.15,
            'timing_risk': 0.15,
            'customer_risk': 0.15,
            'payment_method_risk': 0.10
        }
        
        # Merchant risk categories
        self.merchant_risk_levels = {
            'grocery': 0.1,
            'restaurant': 0.15,
            'gas': 0.1,
            'retail': 0.2,
            'entertainment': 0.25,
            'travel': 0.3,
            'financial': 0.4,
            'healthcare': 0.2,
            'utilities': 0.1,
            'high_risk': 0.9
        }
        
        # Location risk mapping
        self.location_risks = {
            'domestic_common': 0.1,
            'domestic_medium': 0.3,
            'international_safe': 0.4,
            'international_risky': 0.8,
            'unknown': 0.9
        }
        
        # Payment method risks
        self.payment_method_risks = {
            'CREDIT_CARD': 0.1,
            'DEBIT_CARD': 0.15,
            'BANK_TRANSFER': 0.2,
            'DIGITAL_WALLET': 0.3,
            'WIRE_TRANSFER': 0.7,
            'CASH': 0.8,
            'CRYPTOCURRENCY': 0.9,
            'MONEY_ORDER': 0.8,
            'PREPAID_CARD': 0.6
        }
    
    def calculate_risk_score(self, transaction: Dict[str, Any], 
                           customer_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a transaction
        
        Args:
            transaction: Transaction data
            customer_history: Optional customer history from previous tool call
            
        Returns:
            Structured risk assessment
        """
        transaction_id = transaction.get('transaction_id', 'unknown')
        logger.info(f"Calculating risk score for transaction {transaction_id}")
        
        try:
            # Calculate individual risk factors
            risk_factors = {}
            
            # Amount risk
            risk_factors['amount_risk'] = self._calculate_amount_risk(transaction, customer_history)
            
            # Merchant risk  
            risk_factors['merchant_risk'] = self._calculate_merchant_risk(transaction)
            
            # Location risk
            risk_factors['location_risk'] = self._calculate_location_risk(transaction, customer_history)
            
            # Timing risk
            risk_factors['timing_risk'] = self._calculate_timing_risk(transaction)
            
            # Customer behavior risk
            risk_factors['customer_risk'] = self._calculate_customer_risk(transaction, customer_history)
            
            # Payment method risk
            risk_factors['payment_method_risk'] = self._calculate_payment_method_risk(transaction)
            
            # Calculate weighted composite score
            composite_score = sum(
                risk_factors[factor]['score'] * self.risk_weights[factor]
                for factor in self.risk_weights
            )
            
            # Determine risk level
            risk_level = self._determine_risk_level(composite_score)
            
            # Calculate confidence based on available data
            confidence_score = self._calculate_confidence(transaction, customer_history)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_level, risk_factors)
            next_actions = self._generate_next_actions(risk_level, composite_score)
            
            # Create structured assessment
            assessment = RiskAssessment(
                transaction_id=transaction_id,
                overall_risk_score=round(composite_score, 3),
                risk_level=risk_level.value,
                confidence_score=round(confidence_score, 3),
                risk_factors=risk_factors,
                recommendations=recommendations,
                next_actions=next_actions
            )
            
            result = {
                "status": "success",
                "risk_assessment": asdict(assessment),
                "scoring_metadata": {
                    "model_version": "1.0",
                    "scoring_time": datetime.now().isoformat(),
                    "factors_considered": list(self.risk_weights.keys()),
                    "weight_distribution": self.risk_weights
                }
            }
            
            logger.info(f"Risk score calculated for {transaction_id}: "
                       f"{composite_score:.3f} ({risk_level.value})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating risk score for {transaction_id}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "transaction_id": transaction_id
            }
    
    def _calculate_amount_risk(self, transaction: Dict[str, Any], 
                             customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk based on transaction amount"""
        
        amount = float(transaction.get('amount', 0))
        
        # Base amount risk (higher amounts = higher risk)
        base_risk = min(amount / 10000, 0.6)  # Cap at 0.6 for amount alone
        
        # Compare with customer history if available
        history_risk = 0.0
        context = []
        
        if customer_history and customer_history.get('status') == 'success':
            hist_data = customer_history.get('transaction_history', {})
            avg_amount = hist_data.get('average_amount', 0)
            max_amount = hist_data.get('max_amount', 0)
            
            if avg_amount > 0:
                # Risk increases if amount is significantly higher than average
                deviation_factor = amount / avg_amount
                if deviation_factor > 10:
                    history_risk = 0.4
                    context.append(f"Amount is {deviation_factor:.1f}x higher than average")
                elif deviation_factor > 5:
                    history_risk = 0.3
                    context.append(f"Amount is {deviation_factor:.1f}x higher than average")
                elif deviation_factor > 3:
                    history_risk = 0.2
                    context.append(f"Amount is {deviation_factor:.1f}x higher than average")
                elif deviation_factor < 0.1:
                    history_risk = 0.1
                    context.append("Amount is unusually low compared to history")
        
        # Round number risk (exact thousands often suspicious for large amounts)
        round_risk = 0.0
        if amount >= 1000 and amount == int(amount) and amount % 1000 == 0:
            round_risk = 0.15
            context.append("Suspiciously round number for large amount")
        
        # Combine risks
        total_risk = min(base_risk + history_risk + round_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'base_amount_risk': round(base_risk, 3),
                'history_deviation_risk': round(history_risk, 3),
                'round_number_risk': round(round_risk, 3)
            },
            'context': context,
            'details': f"Transaction amount: ${amount:.2f}"
        }
    
    def _calculate_merchant_risk(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk based on merchant category and details"""
        
        merchant_id = transaction.get('merchant_id', '').upper()
        merchant_category = transaction.get('merchant_category', 'unknown')
        
        # Base risk from category
        base_risk = self.merchant_risk_levels.get(merchant_category, 0.5)
        
        # Additional risk factors
        additional_risk = 0.0
        context = []
        
        # Check for high-risk keywords in merchant name
        high_risk_keywords = ['UNKNOWN', 'TEMP', 'CASH', 'CRYPTO', 'GAMBLING', 'CASINO', 'PAWN']
        for keyword in high_risk_keywords:
            if keyword in merchant_id:
                additional_risk += 0.2
                context.append(f"High-risk keyword detected: {keyword}")
        
        # Check for suspicious patterns
        if len(merchant_id) < 3:
            additional_risk += 0.1
            context.append("Unusually short merchant identifier")
        
        if merchant_id.startswith('UNKNOWN') or merchant_id.startswith('TEMP'):
            additional_risk += 0.3
            context.append("Temporary or unknown merchant")
        
        total_risk = min(base_risk + additional_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'category_risk': round(base_risk, 3),
                'merchant_name_risk': round(additional_risk, 3)
            },
            'context': context,
            'details': f"Merchant: {merchant_id} (Category: {merchant_category})"
        }
    
    def _calculate_location_risk(self, transaction: Dict[str, Any], 
                               customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk based on transaction location"""
        
        location = transaction.get('location', {})
        if isinstance(location, str):
            location_str = location
            country = 'Unknown'
            city = 'Unknown'
        else:
            location_str = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
            country = location.get('country', 'Unknown').upper()
            city = location.get('city', 'Unknown')
        
        # Determine location risk category
        base_risk = 0.5  # Default for unknown
        location_category = 'unknown'
        
        if 'USA' in country or country == 'US':
            if any(high_risk_city in city.upper() for high_risk_city in ['LAS VEGAS', 'ATLANTIC CITY']):
                base_risk = 0.3
                location_category = 'domestic_medium'
            else:
                base_risk = 0.1
                location_category = 'domestic_common'
        elif country in ['CANADA', 'UK', 'FRANCE', 'GERMANY', 'JAPAN', 'AUSTRALIA']:
            base_risk = 0.4
            location_category = 'international_safe'
        elif country in ['NIGERIA', 'ROMANIA', 'UKRAINE', 'BANGLADESH', 'PAKISTAN']:
            base_risk = 0.8
            location_category = 'international_risky'
        
        # Historical location analysis
        history_risk = 0.0
        context = []
        
        if customer_history and customer_history.get('status') == 'success':
            hist_data = customer_history.get('transaction_history', {})
            common_locations = hist_data.get('common_locations', [])
            international_ratio = hist_data.get('international_ratio', 0)
            
            # Check if this is a new location
            if location_str not in common_locations:
                if location_category == 'international_risky':
                    history_risk = 0.4
                    context.append("New high-risk international location")
                elif location_category in ['international_safe', 'domestic_medium']:
                    history_risk = 0.2
                    context.append("New location for customer")
                else:
                    history_risk = 0.1
                    context.append("New domestic location")
            
            # Check for sudden international activity
            if 'USA' not in country and international_ratio < 0.1:
                history_risk += 0.2
                context.append("Unusual international activity for domestic customer")
        
        # Geographic impossibility check (simplified)
        geo_risk = 0.0
        if customer_history and customer_history.get('status') == 'success':
            # This would normally check if transaction location is impossible given recent history
            # For demo, we'll add risk for certain country combinations
            if country in ['NIGERIA', 'ROMANIA'] and location_category != 'international_risky':
                geo_risk = 0.3
                context.append("Potentially impossible geographic pattern")
        
        total_risk = min(base_risk + history_risk + geo_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'base_location_risk': round(base_risk, 3),
                'location_history_risk': round(history_risk, 3),
                'geographic_impossibility_risk': round(geo_risk, 3)
            },
            'context': context,
            'details': f"Location: {location_str} (Category: {location_category})"
        }
    
    def _calculate_timing_risk(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk based on transaction timing"""
        
        timestamp_str = transaction.get('timestamp', '')
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return {
                'score': 0.3,
                'components': {'invalid_timestamp_risk': 0.3},
                'context': ["Invalid timestamp format"],
                'details': f"Invalid timestamp: {timestamp_str}"
            }
        
        hour = timestamp.hour
        day_of_week = timestamp.weekday()  # 0 = Monday, 6 = Sunday
        
        # Hour-based risk
        hour_risk = 0.0
        context = []
        
        if 2 <= hour <= 5:  # Very late night / early morning
            hour_risk = 0.6
            context.append(f"Very unusual hour: {hour}:00")
        elif hour <= 1 or hour >= 23:  # Late night
            hour_risk = 0.3
            context.append(f"Late night transaction: {hour}:00")
        elif 6 <= hour <= 22:  # Normal business/personal hours
            hour_risk = 0.05
        else:
            hour_risk = 0.15
        
        # Day of week risk
        day_risk = 0.0
        if day_of_week >= 5:  # Weekend
            amount = float(transaction.get('amount', 0))
            if amount > 1000:  # Large weekend transaction
                day_risk = 0.1
                context.append("Large transaction on weekend")
        
        # Holiday risk (simplified - would check against holiday calendar)
        holiday_risk = 0.0
        # For demo, consider 1st of month as "holiday-like"
        if timestamp.day == 1:
            holiday_risk = 0.05
            context.append("Transaction on first of month")
        
        total_risk = min(hour_risk + day_risk + holiday_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'hour_risk': round(hour_risk, 3),
                'day_of_week_risk': round(day_risk, 3),
                'holiday_risk': round(holiday_risk, 3)
            },
            'context': context,
            'details': f"Time: {timestamp.strftime('%Y-%m-%d %H:%M')} (Hour: {hour}, Day: {day_of_week})"
        }
    
    def _calculate_customer_risk(self, transaction: Dict[str, Any], 
                               customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk based on customer behavior and profile"""
        
        base_risk = 0.5  # Default for unknown customer
        context = []
        
        if not customer_history or customer_history.get('status') != 'success':
            return {
                'score': base_risk,
                'components': {'no_history_risk': base_risk},
                'context': ["No customer history available"],
                'details': "Customer behavior unknown"
            }
        
        # Extract customer profile and history
        profile = customer_history.get('customer_profile', {})
        hist_data = customer_history.get('transaction_history', {})
        
        # Account age risk
        account_age_days = profile.get('account_age_days', 0)
        age_risk = 0.0
        if account_age_days < 30:
            age_risk = 0.4
            context.append(f"Very new account: {account_age_days} days old")
        elif account_age_days < 90:
            age_risk = 0.2
            context.append(f"New account: {account_age_days} days old")
        elif account_age_days < 365:
            age_risk = 0.1
        else:
            age_risk = 0.0
        
        # Verification risk
        verification_risk = 0.0
        verification_status = profile.get('verification_status', 'UNKNOWN')
        if verification_status == 'PARTIAL':
            verification_risk = 0.2
            context.append("Partial customer verification")
        elif verification_status == 'UNVERIFIED':
            verification_risk = 0.4
            context.append("Unverified customer")
        
        # Risk tier
        tier_risk = 0.0
        risk_tier = profile.get('risk_tier', 'MEDIUM')
        if risk_tier == 'HIGH':
            tier_risk = 0.3
            context.append("High-risk customer tier")
        elif risk_tier == 'MEDIUM':
            tier_risk = 0.1
        
        # Behavioral patterns from history
        behavior_risk = 0.0
        risk_indicators = hist_data.get('risk_indicators', [])
        
        if risk_indicators:
            behavior_risk = min(len(risk_indicators) * 0.1, 0.3)
            context.extend(risk_indicators[:3])  # Add first 3 indicators
        
        # Decline history
        decline_risk = 0.0
        total_transactions = hist_data.get('total_transactions', 0)
        declined_transactions = hist_data.get('declined_count', 0)
        
        if total_transactions > 0:
            decline_rate = declined_transactions / total_transactions
            if decline_rate > 0.1:
                decline_risk = min(decline_rate * 0.5, 0.2)
                context.append(f"High decline rate: {decline_rate:.1%}")
        
        total_risk = min(age_risk + verification_risk + tier_risk + behavior_risk + decline_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'account_age_risk': round(age_risk, 3),
                'verification_risk': round(verification_risk, 3),
                'risk_tier_risk': round(tier_risk, 3),
                'behavioral_risk': round(behavior_risk, 3),
                'decline_history_risk': round(decline_risk, 3)
            },
            'context': context,
            'details': f"Customer: {verification_status} {risk_tier}-tier, {account_age_days} days old"
        }
    
    def _calculate_payment_method_risk(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate risk based on payment method"""
        
        payment_method = transaction.get('payment_method', 'UNKNOWN').upper()
        
        # Base risk from payment method
        base_risk = self.payment_method_risks.get(payment_method, 0.5)
        
        context = []
        additional_risk = 0.0
        
        # High-risk method combinations
        amount = float(transaction.get('amount', 0))
        
        if payment_method in ['CASH', 'WIRE_TRANSFER', 'CRYPTOCURRENCY']:
            if amount > 5000:
                additional_risk = 0.2
                context.append(f"Large {payment_method.lower()} transaction")
        
        if payment_method == 'PREPAID_CARD' and amount > 1000:
            additional_risk = 0.15
            context.append("Large prepaid card transaction")
        
        total_risk = min(base_risk + additional_risk, 1.0)
        
        return {
            'score': round(total_risk, 3),
            'components': {
                'base_payment_risk': round(base_risk, 3),
                'amount_method_risk': round(additional_risk, 3)
            },
            'context': context,
            'details': f"Payment method: {payment_method}"
        }
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine categorical risk level from numeric score"""
        if score >= 0.8:
            return RiskLevel.CRITICAL
        elif score >= 0.6:
            return RiskLevel.HIGH
        elif score >= 0.4:
            return RiskLevel.MEDIUM
        elif score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.MINIMAL
    
    def _calculate_confidence(self, transaction: Dict[str, Any], 
                            customer_history: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence in the risk assessment"""
        
        confidence = 0.5  # Base confidence
        
        # Confidence increases with available data
        if customer_history and customer_history.get('status') == 'success':
            hist_data = customer_history.get('transaction_history', {})
            
            # More transaction history = higher confidence
            total_transactions = hist_data.get('total_transactions', 0)
            confidence += min(total_transactions / 100, 0.3)
            
            # Data completeness factor
            data_completeness = hist_data.get('data_completeness', 0)
            confidence += data_completeness * 0.1
            
            # Account age factor
            profile = customer_history.get('customer_profile', {})
            account_age = profile.get('account_age_days', 0)
            confidence += min(account_age / 365, 0.1)
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _generate_recommendations(self, risk_level: RiskLevel, 
                                risk_factors: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on risk assessment"""
        
        recommendations = []
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.extend([
                "BLOCK_TRANSACTION: Immediate blocking recommended",
                "MANUAL_REVIEW: Require immediate fraud team review",
                "CUSTOMER_CONTACT: Contact customer to verify transaction",
                "ACCOUNT_FLAG: Flag customer account for monitoring"
            ])
        elif risk_level == RiskLevel.HIGH:
            recommendations.extend([
                "MANUAL_REVIEW: Route to fraud team for review",
                "ADDITIONAL_VERIFICATION: Require step-up authentication",
                "ENHANCED_MONITORING: Increase account monitoring"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.extend([
                "ADDITIONAL_AUTH: Require additional authentication",
                "TRANSACTION_MONITORING: Monitor subsequent transactions",
                "CONDITIONAL_APPROVAL: Approve with conditions"
            ])
        elif risk_level == RiskLevel.LOW:
            recommendations.extend([
                "APPROVE: Low risk, approve transaction",
                "ROUTINE_MONITORING: Continue routine monitoring"
            ])
        else:  # MINIMAL
            recommendations.extend([
                "AUTO_APPROVE: Very low risk, auto-approve",
                "MINIMAL_MONITORING: Minimal ongoing monitoring"
            ])
        
        # Add specific recommendations based on risk factors
        for factor, data in risk_factors.items():
            if data['score'] > 0.7:
                if factor == 'amount_risk':
                    recommendations.append("Consider amount-based verification")
                elif factor == 'location_risk':
                    recommendations.append("Verify customer location")
                elif factor == 'timing_risk':
                    recommendations.append("Question unusual timing")
                elif factor == 'customer_risk':
                    recommendations.append("Enhanced customer due diligence")
        
        return recommendations
    
    def _generate_next_actions(self, risk_level: RiskLevel, score: float) -> List[str]:
        """Generate specific next actions"""
        
        actions = []
        
        if risk_level == RiskLevel.CRITICAL:
            actions.extend([
                "Immediately block transaction",
                "Escalate to senior fraud analyst",
                "Initiate customer contact protocol",
                "Generate suspicious activity report if confirmed"
            ])
        elif risk_level == RiskLevel.HIGH:
            actions.extend([
                "Hold transaction for manual review",
                "Request additional customer verification",
                "Check against internal watchlists"
            ])
        elif risk_level == RiskLevel.MEDIUM:
            actions.extend([
                "Require step-up authentication",
                "Set transaction monitoring flags",
                "Review customer profile"
            ])
        else:
            actions.extend([
                "Process transaction normally",
                "Update customer risk profile",
                "Continue standard monitoring"
            ])
        
        return actions


class ComplianceTool:
    """Tool for checking regulatory compliance and AML/KYC rules"""
    
    def __init__(self):
        # Compliance thresholds
        self.ctr_threshold = 10000  # Currency Transaction Report
        self.sir_threshold = 5000   # Suspicious Activity Report
        
        # High-risk countries (simplified OFAC list)
        self.high_risk_countries = {
            'IRAN', 'NORTH_KOREA', 'SYRIA', 'CUBA', 'VENEZUELA', 'MYANMAR',
            'BELARUS', 'RUSSIA', 'AFGHANISTAN', 'SOMALIA', 'YEMEN'
        }
        
        # Sanctioned entity patterns (simplified)
        self.sanctioned_patterns = [
            'SANCTIONED', 'BLOCKED', 'SDN', 'OFAC', 'PROHIBITED'
        ]
        
        # PEP indicators (Politically Exposed Persons)
        self.pep_indicators = [
            'GOVERNMENT', 'MINISTER', 'AMBASSADOR', 'SENATOR', 'CONGRESS',
            'MILITARY', 'GENERAL', 'ADMIRAL', 'ROYAL', 'PRINCE'
        ]
    
    def check_compliance_rules(self, transaction: Dict[str, Any], 
                             customer_history: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Check transaction against compliance and regulatory rules
        
        Args:
            transaction: Transaction data
            customer_history: Optional customer history
            
        Returns:
            Structured compliance assessment
        """
        transaction_id = transaction.get('transaction_id', 'unknown')
        logger.info(f"Checking compliance rules for transaction {transaction_id}")
        
        try:
            # Perform individual compliance checks
            aml_result = self._check_aml_rules(transaction, customer_history)
            kyc_result = self._check_kyc_requirements(transaction, customer_history)
            sanctions_result = self._check_sanctions(transaction)
            pep_result = self._check_pep_status(transaction, customer_history)
            
            # Aggregate violations and warnings
            all_violations = []
            all_warnings = []
            
            all_violations.extend(aml_result['violations'])
            all_violations.extend(kyc_result['violations'])
            all_violations.extend(sanctions_result['violations'])
            all_violations.extend(pep_result['violations'])
            
            all_warnings.extend(aml_result['warnings'])
            all_warnings.extend(kyc_result['warnings'])
            all_warnings.extend(sanctions_result['warnings'])
            all_warnings.extend(pep_result['warnings'])
            
            # Determine overall compliance status
            if all_violations:
                overall_status = "VIOLATION"
            elif all_warnings:
                overall_status = "WARNING"
            else:
                overall_status = "COMPLIANT"
            
            # Determine required reports
            required_reports = self._determine_required_reports(transaction, all_violations, all_warnings)
            
            # Generate regulatory flags
            regulatory_flags = self._generate_regulatory_flags(transaction, all_violations, all_warnings)
            
            # Determine if investigation is required
            investigation_required = len(all_violations) > 0 or any(
                'HIGH_RISK' in str(warning) for warning in all_warnings
            )
            
            # Create structured compliance check
            compliance_check = ComplianceCheck(
                transaction_id=transaction_id,
                overall_status=overall_status,
                aml_status=aml_result['status'],
                kyc_status=kyc_result['status'],
                sanctions_status=sanctions_result['status'],
                pep_status=pep_result['status'],
                violations=all_violations,
                warnings=all_warnings,
                required_reports=required_reports,
                regulatory_flags=regulatory_flags,
                investigation_required=investigation_required
            )
            
            result = {
                "status": "success",
                "compliance_check": asdict(compliance_check),
                "detailed_results": {
                    "aml_check": aml_result,
                    "kyc_check": kyc_result,
                    "sanctions_check": sanctions_result,
                    "pep_check": pep_result
                },
                "compliance_metadata": {
                    "check_time": datetime.now().isoformat(),
                    "regulation_version": "2024.1",
                    "jurisdiction": "US"
                }
            }
            
            logger.info(f"Compliance check complete for {transaction_id}: "
                       f"{overall_status} ({len(all_violations)} violations, {len(all_warnings)} warnings)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking compliance for {transaction_id}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "transaction_id": transaction_id
            }
    
    def _check_aml_rules(self, transaction: Dict[str, Any], 
                        customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check Anti-Money Laundering rules"""
        
        violations = []
        warnings = []
        
        amount = float(transaction.get('amount', 0))
        payment_method = transaction.get('payment_method', '').upper()
        merchant_category = transaction.get('merchant_category', '')
        
        # CTR (Currency Transaction Report) requirements
        if amount >= self.ctr_threshold:
            if payment_method in ['CASH', 'MONEY_ORDER']:
                violations.append({
                    'rule': 'BSA_CTR_REQUIRED',
                    'description': f'Cash transaction of ${amount:,.2f} requires CTR filing',
                    'regulation': '31 CFR 1010.311',
                    'severity': 'HIGH'
                })
            else:
                warnings.append({
                    'rule': 'CTR_THRESHOLD_MET',
                    'description': f'Transaction of ${amount:,.2f} meets CTR threshold',
                    'regulation': '31 CFR 1010.311',
                    'severity': 'MEDIUM'
                })
        
        # Structuring detection
        if 9000 <= amount < 10000 and customer_history:
            hist_data = customer_history.get('transaction_history', {})
            # Check for multiple transactions just under CTR threshold
            if self._detect_structuring_pattern(amount, hist_data):
                violations.append({
                    'rule': 'STRUCTURING_SUSPECTED',
                    'description': 'Potential structuring to avoid CTR reporting',
                    'regulation': '31 CFR 1010.100(xx)',
                    'severity': 'CRITICAL'
                })
        
        # High-risk merchant categories
        if merchant_category == 'high_risk':
            warnings.append({
                'rule': 'HIGH_RISK_MERCHANT',
                'description': 'Transaction with high-risk merchant category',
                'regulation': 'AML Program Requirements',
                'severity': 'MEDIUM'
            })
        
        # Money Service Business transactions
        if merchant_category in ['financial', 'high_risk'] and amount >= 3000:
            warnings.append({
                'rule': 'MSB_THRESHOLD',
                'description': 'Large money service business transaction',
                'regulation': '31 CFR 1022',
                'severity': 'MEDIUM'
            })
        
        # Rapid movement of funds
        if customer_history and self._detect_rapid_fund_movement(transaction, customer_history):
            warnings.append({
                'rule': 'RAPID_FUND_MOVEMENT',
                'description': 'Rapid movement of funds detected',
                'regulation': 'AML Suspicious Activity Indicators',
                'severity': 'HIGH'
            })
        
        # Determine AML status
        if violations:
            status = "VIOLATION"
        elif warnings:
            status = "WARNING"
        else:
            status = "COMPLIANT"
        
        return {
            'status': status,
            'violations': violations,
            'warnings': warnings,
            'checks_performed': ['CTR_threshold', 'structuring', 'high_risk_merchant', 'MSB', 'fund_movement']
        }
    
    def _check_kyc_requirements(self, transaction: Dict[str, Any], 
                              customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check Know Your Customer requirements"""
        
        violations = []
        warnings = []
        
        amount = float(transaction.get('amount', 0))
        customer_id = transaction.get('customer_id', '')
        
        # Get customer profile if available
        if customer_history and customer_history.get('status') == 'success':
            profile = customer_history.get('customer_profile', {})
            
            verification_status = profile.get('verification_status', 'UNKNOWN')
            account_age_days = profile.get('account_age_days', 0)
            identity_verified = profile.get('identity_verified', False)
            
            # New customer with large transaction
            if account_age_days < 30 and amount >= 5000:
                if verification_status != 'VERIFIED':
                    violations.append({
                        'rule': 'KYC_NEW_CUSTOMER_LARGE_TXN',
                        'description': f'New customer (age: {account_age_days} days) with large unverified transaction',
                        'regulation': 'Customer Identification Program',
                        'severity': 'HIGH'
                    })
                else:
                    warnings.append({
                        'rule': 'KYC_NEW_CUSTOMER_MONITORING',
                        'description': 'New customer with large transaction requires enhanced monitoring',
                        'regulation': 'Enhanced Due Diligence',
                        'severity': 'MEDIUM'
                    })
            
            # Identity verification requirements
            if not identity_verified and amount >= 3000:
                violations.append({
                    'rule': 'KYC_IDENTITY_VERIFICATION',
                    'description': 'Large transaction requires identity verification',
                    'regulation': '31 CFR 1020.220',
                    'severity': 'MEDIUM'
                })
            
            # Enhanced due diligence triggers
            risk_tier = profile.get('risk_tier', 'UNKNOWN')
            if risk_tier == 'HIGH' and amount >= 1000:
                warnings.append({
                    'rule': 'EDD_HIGH_RISK_CUSTOMER',
                    'description': 'High-risk customer requires enhanced due diligence',
                    'regulation': 'Enhanced Due Diligence Requirements',
                    'severity': 'HIGH'
                })
        
        else:
            # No customer information available
            if amount >= 3000:
                violations.append({
                    'rule': 'KYC_NO_CUSTOMER_INFO',
                    'description': 'Large transaction with no customer verification information',
                    'regulation': 'Customer Identification Program',
                    'severity': 'HIGH'
                })
        
        # Beneficial ownership requirements (for business accounts)
        if customer_id.startswith('BUS_') and amount >= 25000:
            warnings.append({
                'rule': 'BENEFICIAL_OWNERSHIP',
                'description': 'Large business transaction requires beneficial ownership verification',
                'regulation': '31 CFR 1010.230',
                'severity': 'MEDIUM'
            })
        
        # Determine KYC status
        if violations:
            status = "VIOLATION"
        elif warnings:
            status = "WARNING"
        else:
            status = "COMPLIANT"
        
        return {
            'status': status,
            'violations': violations,
            'warnings': warnings,
            'checks_performed': ['new_customer', 'identity_verification', 'enhanced_due_diligence', 'beneficial_ownership']
        }
    
    def _check_sanctions(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Check OFAC sanctions and watchlists"""
        
        violations = []
        warnings = []
        
        # Check location against sanctioned countries
        location = transaction.get('location', {})
        if isinstance(location, dict):
            country = location.get('country', '').upper().replace(' ', '_')
        else:
            # Handle string location format
            country_part = location.split(',')[-1].strip().upper()
            country = country_part.replace(' ', '_')
        
        if country in self.high_risk_countries:
            violations.append({
                'rule': 'OFAC_SANCTIONED_COUNTRY',
                'description': f'Transaction with sanctioned country: {country}',
                'regulation': 'OFAC Sanctions Programs',
                'severity': 'CRITICAL'
            })
        
        # Check merchant against sanctioned entity patterns
        merchant_id = transaction.get('merchant_id', '').upper()
        merchant_name = transaction.get('merchant_name', '').upper()
        
        for pattern in self.sanctioned_patterns:
            if pattern in merchant_id or pattern in merchant_name:
                violations.append({
                    'rule': 'OFAC_SANCTIONED_ENTITY',
                    'description': f'Transaction with potentially sanctioned entity: {merchant_id}',
                    'regulation': 'OFAC SDN List',
                    'severity': 'CRITICAL'
                })
                break
        
        # Check for shell company indicators
        if any(indicator in merchant_id for indicator in ['SHELL', 'TEMP', 'UNKNOWN']):
            warnings.append({
                'rule': 'SHELL_COMPANY_INDICATOR',
                'description': 'Transaction with potential shell company',
                'regulation': 'OFAC Due Diligence',
                'severity': 'HIGH'
            })
        
        # Additional geographical risk checks
        if country in ['AFGHANISTAN', 'MYANMAR', 'BELARUS']:
            warnings.append({
                'rule': 'HIGH_RISK_JURISDICTION',
                'description': f'Transaction with high-risk jurisdiction: {country}',
                'regulation': 'OFAC Geographic Sanctions',
                'severity': 'HIGH'
            })
        
        # Determine sanctions status
        if violations:
            status = "VIOLATION"
        elif warnings:
            status = "WARNING"
        else:
            status = "COMPLIANT"
        
        return {
            'status': status,
            'violations': violations,
            'warnings': warnings,
            'checks_performed': ['sanctioned_countries', 'sanctioned_entities', 'shell_companies', 'geographic_risk']
        }
    
    def _check_pep_status(self, transaction: Dict[str, Any], 
                         customer_history: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for Politically Exposed Persons"""
        
        violations = []
        warnings = []
        
        customer_id = transaction.get('customer_id', '')
        amount = float(transaction.get('amount', 0))
        
        # Simplified PEP check (in production, use dedicated PEP database)
        if customer_history and customer_history.get('status') == 'success':
            profile = customer_history.get('customer_profile', {})
            
            # Check if customer ID or profile indicates PEP status
            if any(indicator in customer_id.upper() for indicator in self.pep_indicators):
                warnings.append({
                    'rule': 'PEP_CUSTOMER_DETECTED',
                    'description': 'Customer may be a Politically Exposed Person',
                    'regulation': 'Enhanced Due Diligence for PEPs',
                    'severity': 'HIGH'
                })
            
            # Large transactions from high-risk tier customers
            risk_tier = profile.get('risk_tier', 'UNKNOWN')
            if risk_tier == 'HIGH' and amount >= 10000:
                warnings.append({
                    'rule': 'PEP_LARGE_TRANSACTION',
                    'description': 'Large transaction from high-risk customer requires PEP screening',
                    'regulation': 'PEP Enhanced Monitoring',
                    'severity': 'MEDIUM'
                })
        
        # International wire transfers require PEP checks
        payment_method = transaction.get('payment_method', '').upper()
        location = transaction.get('location', {})
        
        if isinstance(location, dict):
            country = location.get('country', '').upper()
        else:
            country = location.split(',')[-1].strip().upper()
        
        if payment_method == 'WIRE_TRANSFER' and country != 'USA' and amount >= 3000:
            warnings.append({
                'rule': 'INTERNATIONAL_WIRE_PEP_CHECK',
                'description': 'International wire transfer requires PEP verification',
                'regulation': 'Wire Transfer PEP Requirements',
                'severity': 'MEDIUM'
            })
        
        # Determine PEP status
        if violations:
            status = "VIOLATION"
        elif warnings:
            status = "WARNING"
        else:
            status = "COMPLIANT"
        
        return {
            'status': status,
            'violations': violations,
            'warnings': warnings,
            'checks_performed': ['pep_customer_screening', 'high_risk_transactions', 'international_wires']
        }
    
    def _detect_structuring_pattern(self, amount: float, hist_data: Dict[str, Any]) -> bool:
        """Detect potential structuring to avoid reporting thresholds"""
        
        # Look for multiple transactions just under $10,000 in recent history
        # This is a simplified check - real implementation would be more sophisticated
        
        recent_large_txns = 0
        total_transactions = hist_data.get('total_transactions', 0)
        
        # If customer has pattern of large transactions, check for structuring
        if total_transactions > 10:
            max_amount = hist_data.get('max_amount', 0)
            avg_amount = hist_data.get('average_amount', 0)
            
            # If this transaction is unusual (large but under CTR threshold)
            if amount > avg_amount * 3 and amount < 10000 and max_amount > 8000:
                return True
        
        return False
    
    def _detect_rapid_fund_movement(self, transaction: Dict[str, Any], 
                                  customer_history: Dict[str, Any]) -> bool:
        """Detect rapid movement of funds pattern"""
        
        # Check velocity patterns from history
        hist_data = customer_history.get('transaction_history', {})
        velocity_patterns = hist_data.get('velocity_patterns', {})
        
        max_daily = velocity_patterns.get('max_transactions_per_day', 0)
        avg_daily = velocity_patterns.get('average_transactions_per_day', 0)
        
        # If there's evidence of velocity spikes and this is a large transaction
        amount = float(transaction.get('amount', 0))
        if max_daily > avg_daily * 3 and amount > 5000:
            return True
        
        return False
    
    def _determine_required_reports(self, transaction: Dict[str, Any], 
                                  violations: List[Dict[str, Any]], 
                                  warnings: List[Dict[str, Any]]) -> List[str]:
        """Determine which regulatory reports are required"""
        
        reports = []
        amount = float(transaction.get('amount', 0))
        
        # CTR requirements
        if amount >= self.ctr_threshold:
            payment_method = transaction.get('payment_method', '').upper()
            if payment_method in ['CASH', 'MONEY_ORDER']:
                reports.append('CTR')
        
        # SAR requirements
        if violations or any(warning.get('severity') == 'CRITICAL' for warning in warnings):
            reports.append('SAR')
        
        # OFAC reporting
        if any('OFAC' in str(violation) for violation in violations):
            reports.append('OFAC_REPORT')
        
        # Enhanced monitoring reports
        if any(warning.get('severity') == 'HIGH' for warning in warnings):
            reports.append('ENHANCED_MONITORING')
        
        return reports
    
    def _generate_regulatory_flags(self, transaction: Dict[str, Any], 
                                 violations: List[Dict[str, Any]], 
                                 warnings: List[Dict[str, Any]]) -> List[str]:
        """Generate regulatory flags for the transaction"""
        
        flags = []
        amount = float(transaction.get('amount', 0))
        
        # Amount-based flags
        if amount >= 10000:
            flags.append('CTR_THRESHOLD')
        if amount >= 5000:
            flags.append('SAR_MONITORING')
        
        # Violation-based flags
        if violations:
            flags.append('COMPLIANCE_VIOLATION')
        
        # Warning-based flags
        if warnings:
            flags.append('COMPLIANCE_WARNING')
        
        # Specific regulatory flags
        if any('OFAC' in str(violation) for violation in violations):
            flags.append('SANCTIONS_CHECK')
        
        if any('PEP' in str(warning) for warning in warnings):
            flags.append('PEP_MONITORING')
        
        if any('KYC' in str(violation) for violation in violations):
            flags.append('KYC_DEFICIENCY')
        
        return flags


class AlertTool:
    """Tool for creating and formatting alerts"""
    
    def __init__(self):
        # Alert type configurations
        self.alert_configurations = {
            'FRAUD': {
                'default_priority': AlertPriority.P2_HIGH,
                'assigned_team': 'FRAUD_TEAM',
                'escalation_threshold': 2
            },
            'COMPLIANCE': {
                'default_priority': AlertPriority.P1_CRITICAL,
                'assigned_team': 'COMPLIANCE_TEAM',
                'escalation_threshold': 1
            },
            'AML': {
                'default_priority': AlertPriority.P1_CRITICAL,
                'assigned_team': 'AML_TEAM',
                'escalation_threshold': 1
            },
            'KYC': {
                'default_priority': AlertPriority.P2_HIGH,
                'assigned_team': 'KYC_TEAM',
                'escalation_threshold': 2
            },
            'SANCTIONS': {
                'default_priority': AlertPriority.P1_CRITICAL,
                'assigned_team': 'SANCTIONS_TEAM',
                'escalation_threshold': 0  # Immediate escalation
            },
            'VELOCITY': {
                'default_priority': AlertPriority.P3_MEDIUM,
                'assigned_team': 'MONITORING_TEAM',
                'escalation_threshold': 3
            }
        }
        
        # SLA hours by priority
        self.sla_hours = {
            AlertPriority.P1_CRITICAL: 1,
            AlertPriority.P2_HIGH: 4,
            AlertPriority.P3_MEDIUM: 24,
            AlertPriority.P4_LOW: 48
        }
    
    def create_alert(self, transaction: Dict[str, Any], alert_type: str, 
                    severity: str, reasoning: str, 
                    priority: Optional[str] = None,
                    additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a structured alert with priority and reasoning
        
        Args:
            transaction: Transaction data
            alert_type: Type of alert (FRAUD, COMPLIANCE, AML, etc.)
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            reasoning: Detailed reasoning for the alert
            priority: Optional priority override
            additional_data: Additional alert data
            
        Returns:
            Structured alert data
        """
        transaction_id = transaction.get('transaction_id', 'unknown')
        customer_id = transaction.get('customer_id', 'unknown')
        
        logger.info(f"Creating {alert_type} alert for transaction {transaction_id} (severity: {severity})")
        
        try:
            # Generate alert ID
            alert_id = f"ALT_{alert_type}_{uuid.uuid4().hex[:8].upper()}"
            
            # Determine priority
            if priority:
                alert_priority = AlertPriority(priority)
            else:
                alert_priority = self._determine_priority(alert_type, severity)
            
            # Get configuration for alert type
            config = self.alert_configurations.get(alert_type, {
                'default_priority': AlertPriority.P3_MEDIUM,
                'assigned_team': 'GENERAL_TEAM',
                'escalation_threshold': 2
            })
            
            # Generate title and description
            title = self._generate_alert_title(alert_type, severity, transaction)
            description = self._generate_alert_description(transaction, reasoning, additional_data)
            
            # Generate recommended actions
            recommended_actions = self._generate_recommended_actions(alert_type, severity, transaction)
            
            # Determine escalation requirement
            escalation_required = (
                alert_priority in [AlertPriority.P1_CRITICAL, AlertPriority.P2_HIGH] or
                severity == 'CRITICAL'
            )
            
            # Create alert structure
            alert = Alert(
                alert_id=alert_id,
                transaction_id=transaction_id,
                customer_id=customer_id,
                alert_type=alert_type,
                priority=alert_priority.value,
                severity=severity,
                title=title,
                description=description,
                reasoning=reasoning,
                recommended_actions=recommended_actions,
                assigned_team=config['assigned_team'],
                sla_hours=self.sla_hours[alert_priority],
                escalation_required=escalation_required,
                created_at=datetime.now().isoformat(),
                metadata=self._generate_alert_metadata(transaction, alert_type, additional_data)
            )
            
            result = {
                "status": "success",
                "alert": asdict(alert),
                "delivery_info": {
                    "channels": self._get_delivery_channels(alert_priority, severity),
                    "assigned_teams": self._get_alert_recipients(config['assigned_team'], alert_priority),
                    "processing_schedule": self._get_notification_schedule(alert_priority)
                },
                "escalation_info": {
                    "escalation_required": escalation_required,
                    "escalation_threshold_hours": config['escalation_threshold'],
                    "escalation_team": self._get_escalation_team(alert_type)
                }
            }
            
            logger.info(f"Alert {alert_id} created successfully: {title}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating alert for {transaction_id}: {str(e)}")
            return {
                "status": "error",
                "error_message": str(e),
                "transaction_id": transaction_id
            }
    
    def _determine_priority(self, alert_type: str, severity: str) -> AlertPriority:
        """Determine alert priority based on type and severity"""
        
        # Critical severity always gets high priority
        if severity == 'CRITICAL':
            return AlertPriority.P1_CRITICAL
        
        # High severity considerations
        if severity == 'HIGH':
            if alert_type in ['COMPLIANCE', 'AML', 'SANCTIONS']:
                return AlertPriority.P1_CRITICAL
            else:
                return AlertPriority.P2_HIGH
        
        # Medium severity
        if severity == 'MEDIUM':
            if alert_type in ['COMPLIANCE', 'SANCTIONS']:
                return AlertPriority.P2_HIGH
            else:
                return AlertPriority.P3_MEDIUM
        
        # Low severity
        return AlertPriority.P4_LOW
    
    def _generate_alert_title(self, alert_type: str, severity: str, 
                            transaction: Dict[str, Any]) -> str:
        """Generate a descriptive alert title"""
        
        amount = float(transaction.get('amount', 0))
        merchant = transaction.get('merchant_id', 'Unknown')
        
        title_templates = {
            'FRAUD': f"{severity} Risk Fraud Alert - ${amount:,.2f} transaction at {merchant}",
            'COMPLIANCE': f"{severity} Compliance Violation - Transaction requires review",
            'AML': f"{severity} AML Alert - Suspicious transaction pattern detected",
            'KYC': f"{severity} KYC Alert - Customer verification required",
            'SANCTIONS': f"{severity} Sanctions Alert - OFAC check required",
            'VELOCITY': f"{severity} Velocity Alert - Unusual transaction frequency"
        }
        
        return title_templates.get(alert_type, f"{severity} {alert_type} Alert - Transaction review required")
    
    def _generate_alert_description(self, transaction: Dict[str, Any], reasoning: str, 
                                  additional_data: Optional[Dict[str, Any]]) -> str:
        """Generate detailed alert description"""
        
        description_parts = []
        
        # Transaction summary
        amount = float(transaction.get('amount', 0))
        merchant = transaction.get('merchant_id', 'Unknown')
        location = transaction.get('location', {})
        payment_method = transaction.get('payment_method', 'Unknown')
        
        if isinstance(location, dict):
            location_str = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
        else:
            location_str = location
        
        description_parts.append(f"Transaction Details:")
        description_parts.append(f"- Amount: ${amount:,.2f}")
        description_parts.append(f"- Merchant: {merchant}")
        description_parts.append(f"- Location: {location_str}")
        description_parts.append(f"- Payment Method: {payment_method}")
        description_parts.append("")
        
        # Reasoning
        description_parts.append(f"Alert Reasoning:")
        description_parts.append(reasoning)
        
        # Additional data if provided
        if additional_data:
            description_parts.append("")
            description_parts.append("Additional Information:")
            for key, value in additional_data.items():
                if isinstance(value, (list, dict)):
                    description_parts.append(f"- {key}: {json.dumps(value, indent=2)}")
                else:
                    description_parts.append(f"- {key}: {value}")
        
        return "\n".join(description_parts)
    
    def _generate_recommended_actions(self, alert_type: str, severity: str, 
                                    transaction: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on alert type and severity"""
        
        actions = []
        amount = float(transaction.get('amount', 0))
        
        # Critical severity actions
        if severity == 'CRITICAL':
            actions.extend([
                "IMMEDIATE ACTION: Block transaction",
                "Escalate to senior analyst within 30 minutes",
                "Contact customer immediately",
                "Initiate formal investigation"
            ])
        
        # Alert type specific actions
        if alert_type == 'FRAUD':
            actions.extend([
                "Review customer transaction history",
                "Check for similar patterns across other customers",
                "Consider temporary account restrictions"
            ])
            if amount > 10000:
                actions.append("Consider law enforcement escalation")
        
        elif alert_type == 'COMPLIANCE':
            actions.extend([
                "Review regulatory requirements",
                "Prepare compliance documentation",
                "Consider regulatory reporting"
            ])
        
        elif alert_type == 'AML':
            actions.extend([
                "Conduct enhanced transaction review",
                "Check beneficial ownership information",
                "Consider SAR filing"
            ])
        
        elif alert_type == 'SANCTIONS':
            actions.extend([
                "URGENT: Verify OFAC status immediately",
                "Do not process transaction until cleared",
                "Document all verification steps"
            ])
        
        elif alert_type == 'KYC':
            actions.extend([
                "Request additional customer documentation",
                "Verify customer identity",
                "Update customer risk profile"
            ])
        
        elif alert_type == 'VELOCITY':
            actions.extend([
                "Review transaction velocity patterns",
                "Check for automated/programmatic activity",
                "Consider transaction limits"
            ])
        
        # General actions based on severity
        if severity in ['HIGH', 'CRITICAL']:
            actions.append("Document all investigation steps")
            actions.append("Set enhanced monitoring on account")
        
        return actions
    
    def _generate_alert_metadata(self, transaction: Dict[str, Any], alert_type: str, 
                                additional_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate alert metadata"""
        
        metadata = {
            "alert_version": "1.0",
            "detection_system": "AI_FRAUD_SYSTEM",
            "transaction_amount": float(transaction.get('amount', 0)),
            "transaction_currency": transaction.get('currency', 'USD'),
            "merchant_category": transaction.get('merchant_category', 'unknown'),
            "geographic_region": self._determine_geographic_region(transaction),
            "alert_triggers": additional_data.get('alert_triggers', []) if additional_data else [],
            "confidence_score": additional_data.get('confidence_score', 0.5) if additional_data else 0.5
        }
        
        return metadata
    
    def _determine_geographic_region(self, transaction: Dict[str, Any]) -> str:
        """Determine geographic region for the transaction"""
        
        location = transaction.get('location', {})
        
        if isinstance(location, dict):
            country = location.get('country', 'Unknown').upper()
        else:
            country = location.split(',')[-1].strip().upper()
        
        if country in ['USA', 'US']:
            return 'DOMESTIC'
        elif country in ['CANADA', 'UK', 'FRANCE', 'GERMANY', 'JAPAN', 'AUSTRALIA']:
            return 'INTERNATIONAL_LOW_RISK'
        elif country in ['NIGERIA', 'ROMANIA', 'UKRAINE', 'BANGLADESH']:
            return 'INTERNATIONAL_HIGH_RISK'
        else:
            return 'INTERNATIONAL_UNKNOWN'
    
    def _get_delivery_channels(self, priority: AlertPriority, severity: str) -> List[str]:
        """Get delivery channels based on priority and severity"""
        
        channels = ['CONSOLE', 'DASHBOARD']
        
        # Future enhancement: external notification channels
        # Can be extended to include EMAIL, SMS, SLACK when implemented
        
        return channels
    
    def _get_alert_recipients(self, team: str, priority: AlertPriority) -> List[str]:
        """Get alert recipients based on team and priority"""
        
        # Currently using team names for console/dashboard display
        # Future enhancement: actual recipient lists when notifications implemented
        base_teams = {
            'FRAUD_TEAM': ['FRAUD_ANALYSTS', 'FRAUD_MANAGERS'],
            'COMPLIANCE_TEAM': ['COMPLIANCE_OFFICERS', 'COMPLIANCE_MANAGERS'],
            'AML_TEAM': ['AML_ANALYSTS', 'AML_MANAGERS'],
            'KYC_TEAM': ['KYC_OFFICERS', 'CUSTOMER_OPS'],
            'SANCTIONS_TEAM': ['SANCTIONS_ANALYSTS', 'COMPLIANCE_MANAGERS'],
            'MONITORING_TEAM': ['MONITORING_OPERATORS'],
            'GENERAL_TEAM': ['OPERATIONS_TEAM']
        }
        
        recipients = base_teams.get(team, ['OPERATIONS_TEAM'])
        
        # Add escalation teams for high priority alerts
        if priority in [AlertPriority.P1_CRITICAL, AlertPriority.P2_HIGH]:
            recipients.extend(['SENIOR_MANAGEMENT', 'RISK_DIRECTORS'])
        
        return recipients
    
    def _get_notification_schedule(self, priority: AlertPriority) -> Dict[str, Any]:
        """Get alert processing schedule based on priority"""
        
        schedules = {
            AlertPriority.P1_CRITICAL: {
                'initial_alert': 'immediate',
                'review_intervals': [15, 30, 60],  # minutes
                'escalation_after': 60  # minutes
            },
            AlertPriority.P2_HIGH: {
                'initial_alert': 'immediate',
                'review_intervals': [60, 120],  # minutes
                'escalation_after': 240  # minutes
            },
            AlertPriority.P3_MEDIUM: {
                'initial_alert': 'immediate',
                'review_intervals': [480],  # 8 hours
                'escalation_after': 1440  # 24 hours
            },
            AlertPriority.P4_LOW: {
                'initial_alert': 'next_business_hour',
                'review_intervals': [1440],  # 24 hours
                'escalation_after': 2880  # 48 hours
            }
        }
        
        return schedules.get(priority, schedules[AlertPriority.P3_MEDIUM])
    
    def _get_escalation_team(self, alert_type: str) -> str:
        """Get escalation team for alert type"""
        
        escalation_teams = {
            'FRAUD': 'SENIOR_FRAUD_TEAM',
            'COMPLIANCE': 'COMPLIANCE_MANAGEMENT',
            'AML': 'AML_MANAGEMENT',
            'KYC': 'CUSTOMER_OPS_MANAGEMENT',
            'SANCTIONS': 'LEGAL_TEAM',
            'VELOCITY': 'RISK_MANAGEMENT'
        }
        
        return escalation_teams.get(alert_type, 'SENIOR_MANAGEMENT')


# Export the tools for use by the AI agent
__all__ = [
    'TransactionHistoryTool',
    'RiskCalculatorTool', 
    'ComplianceTool',
    'AlertTool'
]