import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re


class FraudDetectionTools:
    def __init__(self):
        self.suspicious_merchants = [
            'UNKNOWN_MERCHANT',
            'CASH_ADVANCE',
            'GAMBLING',
            'CRYPTO_EXCHANGE'
        ]
        
        self.high_risk_countries = ['XX', 'UNKNOWN', 'IR', 'KP', 'SY']
        
        # Simulated user profiles database
        self.user_profiles = {}
    
    def check_fraud_patterns(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transaction for known fraud patterns"""
        
        indicators = []
        risk_factors = 0
        
        # Check for suspicious merchants
        merchant = transaction.get('merchant_id', '').upper()
        if any(suspicious in merchant for suspicious in self.suspicious_merchants):
            indicators.append(f"Suspicious merchant: {merchant}")
            risk_factors += 2
        
        # Check for high-risk locations
        location = transaction.get('location', {})
        country = location.get('country', '').upper()
        if country in self.high_risk_countries:
            indicators.append(f"High-risk country: {country}")
            risk_factors += 3
        
        # Check for unusual amounts
        amount = transaction.get('amount', 0)
        if amount > 10000:
            indicators.append(f"Large transaction amount: ${amount}")
            risk_factors += 2
        elif amount == round(amount) and amount > 1000:
            indicators.append("Round number large amount (possible money laundering)")
            risk_factors += 1
        
        # Check for unusual timing
        timestamp = transaction.get('timestamp', '')
        if timestamp:
            try:
                tx_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = tx_time.hour
                if hour < 5 or hour > 23:
                    indicators.append(f"Transaction at unusual hour: {hour}:00")
                    risk_factors += 1
            except:
                indicators.append("Invalid timestamp format")
                risk_factors += 1
        
        # Check for velocity patterns
        user_id = transaction.get('user_id')
        if self._check_velocity_fraud(user_id, transaction):
            indicators.append("High transaction velocity detected")
            risk_factors += 3
        
        # Check for geographic impossibility
        if self._check_geographic_impossibility(user_id, transaction):
            indicators.append("Geographic impossibility detected")
            risk_factors += 4
        
        is_suspicious = risk_factors >= 3
        
        return {
            "is_suspicious": is_suspicious,
            "risk_factors_count": risk_factors,
            "indicators": indicators,
            "fraud_score": min(risk_factors * 0.2, 1.0)
        }
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get or create user spending profile"""
        
        if user_id not in self.user_profiles:
            # Create default profile for new user
            self.user_profiles[user_id] = {
                "user_id": user_id,
                "average_transaction_amount": 150.0,
                "typical_merchants": ["GROCERY_STORE", "GAS_STATION", "RESTAURANT"],
                "typical_locations": [
                    {"city": "New York", "state": "NY", "country": "USA"}
                ],
                "transaction_count": 0,
                "last_transaction_time": None,
                "last_location": None,
                "monthly_spending": 3000.0,
                "risk_score_history": [0.1, 0.15, 0.12],
                "account_age_days": 365,
                "verified_phone": True,
                "verified_email": True
            }
        
        return self.user_profiles[user_id]
    
    def update_user_profile(self, user_id: str, transaction: Dict[str, Any]):
        """Update user profile with new transaction data"""
        profile = self.get_user_profile(user_id)
        
        # Update transaction count
        profile["transaction_count"] += 1
        
        # Update last transaction info
        profile["last_transaction_time"] = transaction.get('timestamp')
        profile["last_location"] = transaction.get('location')
        
        # Update typical merchants
        merchant = transaction.get('merchant_id')
        if merchant and merchant not in profile["typical_merchants"]:
            if len(profile["typical_merchants"]) < 10:
                profile["typical_merchants"].append(merchant)
        
        # Update spending patterns
        amount = transaction.get('amount', 0)
        current_avg = profile["average_transaction_amount"]
        count = profile["transaction_count"]
        profile["average_transaction_amount"] = (current_avg * (count - 1) + amount) / count
        
        self.user_profiles[user_id] = profile
    
    def _check_velocity_fraud(self, user_id: str, transaction: Dict[str, Any]) -> bool:
        """Check for velocity-based fraud patterns"""
        # In a real system, this would query a database of recent transactions
        # For demo purposes, we'll simulate some velocity checks
        
        current_time = datetime.now()
        amount = transaction.get('amount', 0)
        
        # Simulate checking if user has made multiple large transactions recently
        if amount > 1000:
            # In real implementation, check if user made >3 transactions >$1000 in last hour
            return False  # Simplified for demo
        
        return False
    
    def _check_geographic_impossibility(self, user_id: str, transaction: Dict[str, Any]) -> bool:
        """Check if transaction location is geographically impossible"""
        profile = self.get_user_profile(user_id)
        last_location = profile.get('last_location')
        current_location = transaction.get('location', {})
        last_time = profile.get('last_transaction_time')
        current_time = transaction.get('timestamp')
        
        if not all([last_location, current_location, last_time, current_time]):
            return False
        
        try:
            last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
            current_dt = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            time_diff = (current_dt - last_dt).total_seconds() / 3600  # hours
            
            # Simple distance check (in real system, use proper geographic distance)
            last_lat = last_location.get('lat', 0)
            last_lon = last_location.get('lon', 0)
            curr_lat = current_location.get('lat', 0)
            curr_lon = current_location.get('lon', 0)
            
            # Rough distance calculation
            lat_diff = abs(curr_lat - last_lat)
            lon_diff = abs(curr_lon - last_lon)
            rough_distance = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 69  # miles
            
            # Check if distance could be traveled in time (assume max 600 mph)
            max_possible_distance = time_diff * 600
            
            return rough_distance > max_possible_distance
            
        except:
            return False
    
    def check_blacklist(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Check if transaction involves blacklisted entities"""
        
        blacklisted_entities = []
        
        # Check merchant blacklist
        merchant = transaction.get('merchant_id', '').upper()
        if 'FRAUD' in merchant or 'SCAM' in merchant:
            blacklisted_entities.append(f"Blacklisted merchant: {merchant}")
        
        # Check user blacklist (simulate)
        user_id = transaction.get('user_id', '')
        if user_id.endswith('999'):  # Demo: users ending in 999 are blacklisted
            blacklisted_entities.append(f"Blacklisted user: {user_id}")
        
        return {
            "is_blacklisted": len(blacklisted_entities) > 0,
            "blacklisted_entities": blacklisted_entities
        }