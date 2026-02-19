#!/usr/bin/env python3
"""
RAG Integration for AI Agent Processor
Integrates fraud pattern knowledge retrieval into the main AI processing workflow
"""

import logging
import os
from typing import Dict, Any, Optional

from agent.rag import FraudPatternSearchTool


logger = logging.getLogger(__name__)


def integrate_rag_with_processor():
    """
    Example integration showing how to add RAG tool to the AI processor
    This updates the processor.py to include the search_fraud_patterns tool
    """
    
    # This is an example of how to modify the TogetherAIClient class
    # to include the RAG tool in the processor.py file
    
    rag_tool_definition = {
        "search_fraud_patterns": {
            "function": None,  # Will be set to actual function instance
            "description": "Search knowledge base of known fraud patterns and detection methods",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Description of fraud indicators, patterns, or behaviors to search for"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of relevant fraud patterns to return (default: 5)"
                    },
                    "pattern_type": {
                        "type": "string", 
                        "description": "Filter by pattern type (CARD_FRAUD, ACCOUNT_FRAUD, MONEY_LAUNDERING, etc.)"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)"
                    }
                },
                "required": ["query"]
            }
        }
    }
    
    return rag_tool_definition


class EnhancedTogetherAIClient:
    """
    Enhanced AI client with RAG integration
    This is an example of how to extend the processor with RAG capabilities
    """
    
    def __init__(self, api_key: str, together_api_key: str):
        # Initialize RAG system
        self.rag_tool = FraudPatternSearchTool(together_api_key)
        
        # Add to available functions (this would be in the actual processor)
        self.available_functions = {
            # ... existing functions from processor.py ...
            
            "search_fraud_patterns": {
                "function": self.rag_tool.search_fraud_patterns,
                "description": "Search knowledge base of known fraud patterns and detection methods",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Description of fraud indicators, patterns, or behaviors to search for"
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of relevant fraud patterns to return (default: 5)"
                        },
                        "pattern_type": {
                            "type": "string", 
                            "description": "Filter by pattern type (CARD_FRAUD, ACCOUNT_FRAUD, MONEY_LAUNDERING, etc.)"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Filter by severity level (LOW, MEDIUM, HIGH, CRITICAL)"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    
    async def enhanced_analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced transaction analysis with RAG-powered fraud pattern matching
        """
        
        # Step 1: Analyze transaction with existing tools
        # (This would call the existing analysis pipeline)
        
        # Step 2: Search for similar fraud patterns
        transaction_description = self._create_transaction_description(transaction)
        
        fraud_patterns = await self.rag_tool.search_fraud_patterns(
            query=transaction_description,
            n_results=3
        )
        
        # Step 3: Enhanced reasoning with pattern knowledge
        enhanced_context = self._create_enhanced_context(transaction, fraud_patterns)
        
        return {
            "transaction_analysis": "...",  # Existing analysis
            "fraud_pattern_matches": fraud_patterns,
            "enhanced_context": enhanced_context
        }
    
    def _create_transaction_description(self, transaction: Dict[str, Any]) -> str:
        """Create a description of the transaction for pattern matching"""
        
        amount = transaction.get('amount', 0)
        merchant = transaction.get('merchant_id', 'Unknown')
        location = transaction.get('location', {})
        payment_method = transaction.get('payment_method', 'Unknown')
        
        if isinstance(location, dict):
            location_str = f"{location.get('city', 'Unknown')}, {location.get('country', 'Unknown')}"
        else:
            location_str = str(location)
        
        description = f"""
        Transaction with amount ${amount} at merchant {merchant} 
        in location {location_str} using payment method {payment_method}.
        Looking for similar fraud patterns involving large amounts, 
        unusual merchants, international transactions, or suspicious payment methods.
        """
        
        return description.strip()
    
    def _create_enhanced_context(self, transaction: Dict[str, Any], 
                               fraud_patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Create enhanced context combining transaction and pattern knowledge"""
        
        context = {
            "transaction_summary": {
                "amount": transaction.get('amount'),
                "merchant": transaction.get('merchant_id'),
                "location": transaction.get('location'),
                "payment_method": transaction.get('payment_method')
            },
            "pattern_insights": [],
            "risk_factors_identified": [],
            "recommended_actions": []
        }
        
        if fraud_patterns.get('status') == 'success':
            for pattern in fraud_patterns.get('results', []):
                insight = {
                    "pattern_type": pattern.get('pattern_type'),
                    "similarity_score": pattern.get('similarity_score'),
                    "relevant_indicators": self._extract_relevant_indicators(transaction, pattern),
                    "pattern_title": pattern.get('title')
                }
                context["pattern_insights"].append(insight)
        
        return context
    
    def _extract_relevant_indicators(self, transaction: Dict[str, Any], 
                                   pattern: Dict[str, Any]) -> List[str]:
        """Extract indicators from the pattern that might apply to this transaction"""
        
        # This would implement logic to match transaction characteristics
        # with pattern indicators and return relevant ones
        
        relevant = []
        
        amount = float(transaction.get('amount', 0))
        if amount > 10000 and 'large' in pattern.get('content_preview', '').lower():
            relevant.append("Large transaction amount")
        
        if 'international' in str(transaction.get('location', '')).lower():
            if 'international' in pattern.get('content_preview', '').lower():
                relevant.append("International transaction")
        
        return relevant


# Example usage and integration instructions
def setup_rag_integration():
    """
    Setup instructions for integrating RAG into the main processor
    """
    
    instructions = """
    To integrate RAG into your main processor (agent/processor.py):
    
    1. Import the RAG tool:
       from agent.rag import FraudPatternSearchTool
    
    2. Initialize in TogetherAIClient.__init__():
       self.fraud_pattern_tool = FraudPatternSearchTool(self.api_key)
    
    3. Add to available_functions dictionary:
       "search_fraud_patterns": {
           "function": self.fraud_pattern_tool.search_fraud_patterns,
           "description": "Search knowledge base of known fraud patterns",
           "parameters": {
               "type": "object",
               "properties": {
                   "query": {"type": "string", "description": "Fraud pattern query"},
                   "n_results": {"type": "integer", "description": "Number of results"},
                   "pattern_type": {"type": "string", "description": "Filter by type"},
                   "severity": {"type": "string", "description": "Filter by severity"}
               },
               "required": ["query"]
           }
       }
    
    4. Update system prompt to mention the search_fraud_patterns tool:
       "You have access to a knowledge base of fraud patterns. Use search_fraud_patterns 
        to find similar cases and detection methods when analyzing suspicious transactions."
    
    5. The AI will automatically use this tool when it detects patterns that match
       known fraud scenarios in the knowledge base.
    """
    
    return instructions


if __name__ == "__main__":
    print(setup_rag_integration())