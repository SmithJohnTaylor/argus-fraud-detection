import json
import os
from typing import Dict, Any, List, Optional
from together import Together
from tools.fraud_detection import FraudDetectionTools
from tools.risk_analysis import RiskAnalysisTools
from tools.notification import NotificationTools


class TogetherAIAgent:
    def __init__(self, api_key: str = None):
        self.client = Together(api_key=api_key or os.getenv('TOGETHER_API_KEY'))
        self.fraud_tools = FraudDetectionTools()
        self.risk_tools = RiskAnalysisTools()
        self.notification_tools = NotificationTools()
        
        self.available_tools = {
            "check_fraud_patterns": {
                "function": self.fraud_tools.check_fraud_patterns,
                "description": "Analyze transaction for fraud patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction data to analyze"
                        }
                    },
                    "required": ["transaction"]
                }
            },
            "calculate_risk_score": {
                "function": self.risk_tools.calculate_risk_score,
                "description": "Calculate comprehensive risk score for transaction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction": {
                            "type": "object",
                            "description": "Transaction data to analyze"
                        },
                        "user_history": {
                            "type": "array",
                            "description": "Historical transactions for the user"
                        }
                    },
                    "required": ["transaction"]
                }
            },
            "send_alert": {
                "function": self.notification_tools.send_alert,
                "description": "Send fraud alert notification",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "transaction_id": {
                            "type": "string",
                            "description": "ID of the suspicious transaction"
                        },
                        "risk_level": {
                            "type": "string",
                            "description": "Risk level (LOW, MEDIUM, HIGH, CRITICAL)"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for the alert"
                        }
                    },
                    "required": ["transaction_id", "risk_level", "reason"]
                }
            },
            "get_user_profile": {
                "function": self.fraud_tools.get_user_profile,
                "description": "Get user spending profile and behavior patterns",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID to analyze"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }
    
    def format_tools_for_api(self) -> List[Dict[str, Any]]:
        """Format tools for Together AI API"""
        tools = []
        for name, tool_info in self.available_tools.items():
            tools.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool_info["description"],
                    "parameters": tool_info["parameters"]
                }
            })
        return tools
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool function"""
        if tool_name not in self.available_tools:
            return f"Tool {tool_name} not found"
        
        try:
            return self.available_tools[tool_name]["function"](**arguments)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def analyze_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a transaction using Together AI with tool calling"""
        
        system_prompt = """You are a financial fraud detection expert. Analyze the given transaction and determine if it's suspicious.

Use the available tools to:
1. Check for fraud patterns
2. Calculate risk scores  
3. Get user profile information
4. Send alerts if needed

Provide a comprehensive analysis with risk assessment and recommended actions."""

        user_message = f"""Analyze this financial transaction:
{json.dumps(transaction, indent=2)}

Please use the available tools to perform a thorough fraud analysis."""

        try:
            response = self.client.chat.completions.create(
                model=os.getenv('TOGETHER_MODEL', "mistralai/Mixtral-8x7B-Instruct-v0.1"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                tools=self.format_tools_for_api(),
                tool_choice="auto",
                max_tokens=2000,
                temperature=0.1
            )
            
            return self._process_response(response, transaction)
            
        except Exception as e:
            return {
                "error": f"Failed to analyze transaction: {str(e)}",
                "transaction_id": transaction.get("transaction_id"),
                "status": "error"
            }
    
    def _process_response(self, response, original_transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Process the AI response and execute any tool calls"""
        
        result = {
            "transaction_id": original_transaction.get("transaction_id"),
            "analysis": {},
            "tool_results": {},
            "recommendations": [],
            "risk_level": "UNKNOWN"
        }
        
        # Check if the response contains tool calls
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # Execute the tool
                tool_result = self.execute_tool(tool_name, arguments)
                result["tool_results"][tool_name] = tool_result
                
                # Process specific tool results
                if tool_name == "calculate_risk_score" and isinstance(tool_result, dict):
                    result["risk_level"] = tool_result.get("risk_level", "UNKNOWN")
                    result["analysis"]["risk_score"] = tool_result.get("risk_score", 0)
                
                if tool_name == "check_fraud_patterns" and isinstance(tool_result, dict):
                    result["analysis"]["fraud_indicators"] = tool_result.get("indicators", [])
                    result["analysis"]["is_suspicious"] = tool_result.get("is_suspicious", False)
        
        # Get the final AI analysis
        if response.choices[0].message.content:
            result["ai_analysis"] = response.choices[0].message.content
        
        # Generate recommendations based on risk level
        risk_level = result.get("risk_level", "UNKNOWN")
        if risk_level in ["HIGH", "CRITICAL"]:
            result["recommendations"].extend([
                "Block transaction pending manual review",
                "Notify fraud team immediately",
                "Contact customer for verification"
            ])
        elif risk_level == "MEDIUM":
            result["recommendations"].extend([
                "Flag for additional monitoring",
                "Require additional authentication"
            ])
        
        return result


if __name__ == "__main__":
    # Example usage
    agent = TogetherAIAgent()
    
    sample_transaction = {
        "transaction_id": "txn_123456",
        "user_id": "user_789",
        "amount": 5000.00,
        "currency": "USD",
        "merchant_id": "UNKNOWN_MERCHANT",
        "location": {"city": "Unknown", "country": "XX"},
        "timestamp": "2024-01-15T02:30:00",
        "payment_method": "CREDIT_CARD"
    }
    
    result = agent.analyze_transaction(sample_transaction)
    print(json.dumps(result, indent=2))