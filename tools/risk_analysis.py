import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from tools.fraud_detection import FraudDetectionTools


class RiskAnalysisTools:
    def __init__(self):
        self.fraud_tools = FraudDetectionTools()
        
        # Risk scoring weights
        self.weights = {
            'amount': 0.25,
            'location': 0.20,
            'time': 0.15,
            'merchant': 0.15,
            'user_behavior': 0.15,
            'velocity': 0.10
        }
    
    def calculate_risk_score(self, transaction: Dict[str, Any], user_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate comprehensive risk score for a transaction"""
        
        if user_history is None:
            user_history = []
        
        # Get user profile
        user_id = transaction.get('user_id')
        user_profile = self.fraud_tools.get_user_profile(user_id)
        
        # Calculate individual risk components
        amount_risk = self._calculate_amount_risk(transaction, user_profile)
        location_risk = self._calculate_location_risk(transaction, user_profile)
        time_risk = self._calculate_time_risk(transaction)
        merchant_risk = self._calculate_merchant_risk(transaction, user_profile)
        behavior_risk = self._calculate_behavior_risk(transaction, user_profile, user_history)
        velocity_risk = self._calculate_velocity_risk(transaction, user_history)
        
        # Calculate weighted final score
        final_score = (
            amount_risk * self.weights['amount'] +
            location_risk * self.weights['location'] +
            time_risk * self.weights['time'] +
            merchant_risk * self.weights['merchant'] +
            behavior_risk * self.weights['user_behavior'] +
            velocity_risk * self.weights['velocity']
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(final_score)
        
        # Update user profile
        self.fraud_tools.update_user_profile(user_id, transaction)
        
        return {
            "risk_score": round(final_score, 3),
            "risk_level": risk_level,
            "components": {
                "amount_risk": round(amount_risk, 3),
                "location_risk": round(location_risk, 3),
                "time_risk": round(time_risk, 3),
                "merchant_risk": round(merchant_risk, 3),
                "behavior_risk": round(behavior_risk, 3),
                "velocity_risk": round(velocity_risk, 3)
            },
            "confidence": self._calculate_confidence(user_profile),
            "recommendation": self._get_recommendation(risk_level, final_score)
        }
    
    def _calculate_amount_risk(self, transaction: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Calculate risk based on transaction amount"""
        amount = transaction.get('amount', 0)
        avg_amount = user_profile.get('average_transaction_amount', 150)
        monthly_spending = user_profile.get('monthly_spending', 3000)
        
        # Risk increases with amount size
        base_risk = min(amount / 10000, 0.5)  # Cap at 0.5 for amounts
        
        # Risk increases if amount is significantly higher than user's average
        if avg_amount > 0:
            deviation_factor = amount / avg_amount
            if deviation_factor > 3:
                base_risk += min(deviation_factor * 0.1, 0.3)
        
        # Risk increases if amount is large portion of monthly spending
        if monthly_spending > 0:
            monthly_ratio = amount / monthly_spending
            if monthly_ratio > 0.5:
                base_risk += min(monthly_ratio * 0.2, 0.2)
        
        return min(base_risk, 1.0)
    
    def _calculate_location_risk(self, transaction: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Calculate risk based on transaction location"""
        location = transaction.get('location', {})
        typical_locations = user_profile.get('typical_locations', [])
        
        country = location.get('country', '').upper()
        city = location.get('city', '').upper()
        
        # High risk countries
        high_risk_countries = ['XX', 'UNKNOWN', 'IR', 'KP', 'SY', 'AF']
        if country in high_risk_countries:
            return 0.8
        
        # Check if location matches user's typical locations
        location_match = False
        for typical_loc in typical_locations:
            if (typical_loc.get('country', '').upper() == country and
                typical_loc.get('city', '').upper() == city):
                location_match = True
                break
        
        if location_match:
            return 0.1
        elif country == 'USA':
            return 0.2  # Domestic but new location
        else:
            return 0.4  # International location
    
    def _calculate_time_risk(self, transaction: Dict[str, Any]) -> float:
        """Calculate risk based on transaction timing"""
        timestamp = transaction.get('timestamp', '')
        
        try:
            tx_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = tx_time.hour
            day_of_week = tx_time.weekday()  # 0=Monday, 6=Sunday
            
            # Higher risk for unusual hours
            if 2 <= hour <= 5:  # Very late night
                time_risk = 0.6
            elif hour >= 23 or hour <= 1:  # Late night
                time_risk = 0.4
            elif 6 <= hour <= 22:  # Normal business hours
                time_risk = 0.1
            else:
                time_risk = 0.2
            
            # Slightly higher risk on weekends for large transactions
            amount = transaction.get('amount', 0)
            if day_of_week >= 5 and amount > 1000:  # Weekend large transaction
                time_risk += 0.1
            
            return min(time_risk, 1.0)
            
        except:
            return 0.3  # Invalid timestamp
    
    def _calculate_merchant_risk(self, transaction: Dict[str, Any], user_profile: Dict[str, Any]) -> float:
        """Calculate risk based on merchant"""
        merchant = transaction.get('merchant_id', '').upper()
        typical_merchants = user_profile.get('typical_merchants', [])
        
        # High-risk merchant categories
        high_risk_merchants = [
            'UNKNOWN_MERCHANT', 'CASH_ADVANCE', 'GAMBLING', 
            'CRYPTO_EXCHANGE', 'MONEY_TRANSFER', 'PAWN_SHOP'
        ]
        
        if any(risky in merchant for risky in high_risk_merchants):
            return 0.7
        
        # Check if merchant is typical for user
        if merchant in [m.upper() for m in typical_merchants]:
            return 0.1
        
        # New merchant but in safe categories
        safe_merchants = ['GROCERY', 'GAS_STATION', 'RESTAURANT', 'PHARMACY']
        if any(safe in merchant for safe in safe_merchants):
            return 0.2
        
        return 0.3  # Unknown new merchant
    
    def _calculate_behavior_risk(self, transaction: Dict[str, Any], user_profile: Dict[str, Any], user_history: List[Dict[str, Any]]) -> float:
        """Calculate risk based on user behavior patterns"""
        account_age = user_profile.get('account_age_days', 0)
        transaction_count = user_profile.get('transaction_count', 0)
        risk_history = user_profile.get('risk_score_history', [])
        
        behavior_risk = 0.0
        
        # New account risk
        if account_age < 30:
            behavior_risk += 0.3
        elif account_age < 90:
            behavior_risk += 0.1
        
        # Low transaction count risk
        if transaction_count < 10:
            behavior_risk += 0.2
        elif transaction_count < 50:
            behavior_risk += 0.1
        
        # Historical risk pattern
        if risk_history:
            avg_historical_risk = sum(risk_history) / len(risk_history)
            if avg_historical_risk > 0.5:
                behavior_risk += 0.3
            elif avg_historical_risk > 0.3:
                behavior_risk += 0.1
        
        # Verification status
        if not user_profile.get('verified_phone', False):
            behavior_risk += 0.1
        if not user_profile.get('verified_email', False):
            behavior_risk += 0.1
        
        return min(behavior_risk, 1.0)
    
    def _calculate_velocity_risk(self, transaction: Dict[str, Any], user_history: List[Dict[str, Any]]) -> float:
        """Calculate risk based on transaction velocity"""
        if not user_history:
            return 0.1
        
        current_time = datetime.now()
        amount = transaction.get('amount', 0)
        
        # Count recent transactions
        hour_count = 0
        day_count = 0
        hour_amount = 0
        day_amount = 0
        
        for hist_tx in user_history:
            try:
                hist_time = datetime.fromisoformat(hist_tx.get('timestamp', '').replace('Z', '+00:00'))
                time_diff = (current_time - hist_time).total_seconds()
                hist_amount = hist_tx.get('amount', 0)
                
                if time_diff <= 3600:  # 1 hour
                    hour_count += 1
                    hour_amount += hist_amount
                
                if time_diff <= 86400:  # 1 day
                    day_count += 1
                    day_amount += hist_amount
                    
            except:
                continue
        
        velocity_risk = 0.0
        
        # Transaction count velocity
        if hour_count > 5:
            velocity_risk += 0.4
        elif hour_count > 2:
            velocity_risk += 0.2
        
        if day_count > 20:
            velocity_risk += 0.3
        elif day_count > 10:
            velocity_risk += 0.1
        
        # Amount velocity
        if hour_amount > 5000:
            velocity_risk += 0.3
        if day_amount > 20000:
            velocity_risk += 0.2
        
        return min(velocity_risk, 1.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine categorical risk level from numeric score"""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        elif risk_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _calculate_confidence(self, user_profile: Dict[str, Any]) -> float:
        """Calculate confidence in risk assessment"""
        transaction_count = user_profile.get('transaction_count', 0)
        account_age = user_profile.get('account_age_days', 0)
        
        # Confidence increases with more data
        count_confidence = min(transaction_count / 100, 0.5)
        age_confidence = min(account_age / 365, 0.3)
        verification_confidence = 0.0
        
        if user_profile.get('verified_phone', False):
            verification_confidence += 0.1
        if user_profile.get('verified_email', False):
            verification_confidence += 0.1
        
        total_confidence = count_confidence + age_confidence + verification_confidence
        return min(total_confidence, 1.0)
    
    def _get_recommendation(self, risk_level: str, risk_score: float) -> str:
        """Get recommendation based on risk assessment"""
        if risk_level == "CRITICAL":
            return "BLOCK_TRANSACTION - Immediate manual review required"
        elif risk_level == "HIGH":
            return "MANUAL_REVIEW - Hold transaction for fraud team review"
        elif risk_level == "MEDIUM":
            return "ADDITIONAL_AUTH - Require step-up authentication"
        elif risk_level == "LOW":
            return "MONITOR - Flag for monitoring but allow transaction"
        else:
            return "APPROVE - Process transaction normally"