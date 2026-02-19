#!/usr/bin/env python3
"""
End-to-End Test Suite for Financial Transaction Monitoring System
Tests the complete pipeline from transaction generation to AI decisions
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

from confluent_kafka import Producer, Consumer, KafkaError

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.generator import TransactionGenerator
from agent.rag import FraudPatternRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class E2ETestSuite:
    """End-to-end test suite for the fraud detection system"""
    
    def __init__(self):
        self.kafka_config = {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092'),
            'security.protocol': os.getenv('CONFLUENT_SECURITY_PROTOCOL', 'SASL_SSL'),
            'sasl.mechanism': os.getenv('CONFLUENT_SASL_MECHANISM', 'PLAIN'),
            'sasl.username': os.getenv('CONFLUENT_API_KEY'),
            'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
            'ssl.endpoint.identification.algorithm': os.getenv('CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM', 'https'),
            'client.id': 'e2e-test-client'
        }
        
        self.consumer_config = {
            **self.kafka_config,
            'group.id': f'e2e-test-group-{uuid.uuid4().hex[:8]}',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': False
        }
        
        self.producer = None
        self.consumers = {}
        self.processes = {}
        self.test_results = {
            'transactions_sent': 0,
            'decisions_received': 0,
            'tool_calls_validated': 0,
            'assertions_passed': 0,
            'assertions_failed': 0,
            'test_duration': 0
        }
        
        # Test scenarios
        self.test_scenarios = self._create_test_scenarios()
        
    def _create_test_scenarios(self) -> List[Dict[str, Any]]:
        """Create test transaction scenarios"""
        return [
            {
                'name': 'normal_transaction',
                'description': 'Low-risk normal transaction',
                'transaction': {
                    'transaction_id': f'TEST_NORMAL_{uuid.uuid4().hex[:8]}',
                    'customer_id': 'CUST_0001',
                    'amount': 50.00,
                    'currency': 'USD',
                    'merchant_id': 'STARBUCKS',
                    'merchant_name': 'Starbucks Coffee',
                    'merchant_category': 'restaurant',
                    'location': {
                        'city': 'New York',
                        'state': 'NY',
                        'country': 'USA',
                        'latitude': 40.7128,
                        'longitude': -74.0060,
                        'timezone': 'America/New_York'
                    },
                    'payment_method': 'CREDIT_CARD',
                    'timestamp': datetime.now().isoformat(),
                    'device_id': 'DEV_123456',
                    'ip_address': '192.168.1.100'
                },
                'expected_risk_level': 'LOW',
                'expected_decision': 'APPROVE',
                'expected_tools': ['check_transaction_history', 'calculate_risk_score']
            },
            {
                'name': 'high_amount_transaction',
                'description': 'Large amount transaction requiring review',
                'transaction': {
                    'transaction_id': f'TEST_HIGH_AMT_{uuid.uuid4().hex[:8]}',
                    'customer_id': 'CUST_0002',
                    'amount': 15000.00,
                    'currency': 'USD',
                    'merchant_id': 'LUXURY_STORE',
                    'merchant_name': 'High-End Retailer',
                    'merchant_category': 'retail',
                    'location': {
                        'city': 'Beverly Hills',
                        'state': 'CA',
                        'country': 'USA',
                        'latitude': 34.0736,
                        'longitude': -118.4004,
                        'timezone': 'America/Los_Angeles'
                    },
                    'payment_method': 'CREDIT_CARD',
                    'timestamp': datetime.now().isoformat(),
                    'device_id': 'DEV_789012',
                    'ip_address': '10.0.0.50'
                },
                'expected_risk_level': 'MEDIUM',
                'expected_decision': 'MANUAL_REVIEW',
                'expected_tools': ['check_transaction_history', 'calculate_risk_score', 'check_compliance_rules']
            },
            {
                'name': 'suspicious_international',
                'description': 'High-risk international transaction',
                'transaction': {
                    'transaction_id': f'TEST_INTL_{uuid.uuid4().hex[:8]}',
                    'customer_id': 'CUST_0003',
                    'amount': 5000.00,
                    'currency': 'USD',
                    'merchant_id': 'UNKNOWN_MERCHANT',
                    'merchant_name': 'Unknown Merchant',
                    'merchant_category': 'high_risk',
                    'location': {
                        'city': 'Lagos',
                        'state': '',
                        'country': 'Nigeria',
                        'latitude': 6.5244,
                        'longitude': 3.3792,
                        'timezone': 'Africa/Lagos'
                    },
                    'payment_method': 'WIRE_TRANSFER',
                    'timestamp': datetime.now().isoformat(),
                    'device_id': 'DEV_UNKNOWN',
                    'ip_address': '197.210.x.x'
                },
                'expected_risk_level': 'HIGH',
                'expected_decision': 'DECLINE',
                'expected_tools': ['check_transaction_history', 'calculate_risk_score', 'check_compliance_rules', 'create_alert']
            },
            {
                'name': 'velocity_fraud',
                'description': 'Multiple small transactions (card testing)',
                'transaction': {
                    'transaction_id': f'TEST_VELOCITY_{uuid.uuid4().hex[:8]}',
                    'customer_id': 'CUST_0004',
                    'amount': 1.00,
                    'currency': 'USD',
                    'merchant_id': 'ONLINE_SHOP',
                    'merchant_name': 'E-commerce Store',
                    'merchant_category': 'retail',
                    'location': {
                        'city': 'Unknown',
                        'state': '',
                        'country': 'Unknown',
                        'latitude': 0.0,
                        'longitude': 0.0,
                        'timezone': 'UTC'
                    },
                    'payment_method': 'CREDIT_CARD',
                    'timestamp': datetime.now().isoformat(),
                    'device_id': 'DEV_SHARED',
                    'ip_address': '45.123.x.x'
                },
                'expected_risk_level': 'MEDIUM',
                'expected_decision': 'MANUAL_REVIEW',
                'expected_tools': ['check_transaction_history', 'calculate_risk_score', 'search_fraud_patterns']
            },
            {
                'name': 'late_night_crypto',
                'description': 'Late night cryptocurrency purchase',
                'transaction': {
                    'transaction_id': f'TEST_CRYPTO_{uuid.uuid4().hex[:8]}',
                    'customer_id': 'CUST_0005',
                    'amount': 10000.00,
                    'currency': 'USD',
                    'merchant_id': 'CRYPTO_EXCHANGE',
                    'merchant_name': 'CryptoMax Exchange',
                    'merchant_category': 'high_risk',
                    'location': {
                        'city': 'Miami',
                        'state': 'FL',
                        'country': 'USA',
                        'latitude': 25.7617,
                        'longitude': -80.1918,
                        'timezone': 'America/New_York'
                    },
                    'payment_method': 'BANK_TRANSFER',
                    'timestamp': datetime.now().replace(hour=3, minute=30).isoformat(),
                    'device_id': 'DEV_MOBILE',
                    'ip_address': '72.229.x.x'
                },
                'expected_risk_level': 'CRITICAL',
                'expected_decision': 'DECLINE',
                'expected_tools': ['check_transaction_history', 'calculate_risk_score', 'check_compliance_rules', 'create_alert', 'search_fraud_patterns']
            }
        ]
    
    async def setup_infrastructure(self) -> bool:
        """Setup test infrastructure"""
        logger.info("Setting up test infrastructure...")
        
        try:
            # Check if Kafka is running
            if not await self._check_kafka_health():
                logger.error("Kafka is not healthy. Please start docker-compose services.")
                return False
            
            # Initialize Kafka producer
            self.producer = Producer(self.kafka_config)
            
            # Topics should already exist in Confluent Cloud
            
            # Initialize consumers
            await self._setup_consumers()
            
            # Verify RAG system
            await self._verify_rag_system()
            
            logger.info("Infrastructure setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Infrastructure setup failed: {e}")
            return False
    
    async def _check_kafka_health(self) -> bool:
        """Check if Kafka is healthy"""
        try:
            # Simple connection test - just create a producer and flush
            producer = Producer(self.kafka_config)
            producer.flush(timeout=10)
            logger.info("Kafka health check passed")
            return True
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
    
    # Topics are pre-created in Confluent Cloud
    
    async def _setup_consumers(self):
        """Setup Kafka consumers for test validation"""
        # Consumer for AI decisions
        self.consumers['decisions'] = Consumer({
            **self.consumer_config,
            'group.id': f'e2e-decisions-{uuid.uuid4().hex[:8]}'
        })
        self.consumers['decisions'].subscribe(['ai-decisions'])
        
        # Consumer for alerts
        self.consumers['alerts'] = Consumer({
            **self.consumer_config,
            'group.id': f'e2e-alerts-{uuid.uuid4().hex[:8]}'
        })
        self.consumers['alerts'].subscribe(['alerts'])
        
        logger.info("Kafka consumers setup completed")
    
    async def _verify_rag_system(self):
        """Verify RAG system is working"""
        try:
            # Test with a placeholder API key for structure verification
            rag = FraudPatternRAG("test_api_key")
            stats = rag.get_collection_stats()
            
            if stats.get('total_patterns', 0) > 0:
                logger.info(f"RAG system verified: {stats['total_patterns']} fraud patterns loaded")
            else:
                logger.warning("RAG system has no patterns loaded")
                
        except Exception as e:
            logger.warning(f"RAG system verification failed: {e}")
    
    async def start_services(self) -> Dict[str, bool]:
        """Start the fraud detection services"""
        logger.info("Starting fraud detection services...")
        
        services_status = {}
        
        try:
            # Start AI agent processor
            logger.info("Starting AI agent processor...")
            agent_process = await self._start_agent_processor()
            if agent_process:
                self.processes['agent'] = agent_process
                services_status['agent'] = True
                logger.info("AI agent processor started successfully")
            else:
                services_status['agent'] = False
                logger.error("Failed to start AI agent processor")
            
            # Wait for services to initialize
            await asyncio.sleep(5)
            
            return services_status
            
        except Exception as e:
            logger.error(f"Failed to start services: {e}")
            return {'agent': False}
    
    async def _start_agent_processor(self) -> Optional[subprocess.Popen]:
        """Start the AI agent processor"""
        try:
            # Set environment variables for testing
            env = os.environ.copy()
            env.update({
                'TOGETHER_API_KEY': 'test_key_placeholder',
                'CONFLUENT_BOOTSTRAP_SERVERS': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS', 'localhost:9092'),
                'CONFLUENT_SECURITY_PROTOCOL': os.getenv('CONFLUENT_SECURITY_PROTOCOL', 'SASL_SSL'),
                'CONFLUENT_SASL_MECHANISM': os.getenv('CONFLUENT_SASL_MECHANISM', 'PLAIN'),
                'CONFLUENT_API_KEY': os.getenv('CONFLUENT_API_KEY'),
                'CONFLUENT_API_SECRET': os.getenv('CONFLUENT_API_SECRET'),
                'CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM': os.getenv('CONFLUENT_SSL_ENDPOINT_IDENTIFICATION_ALGORITHM', 'https'),
                'KAFKA_TOPIC': 'financial-transactions',
                'KAFKA_OUTPUT_TOPIC': 'ai-decisions',
                'KAFKA_GROUP_ID': 'e2e-test-agent-group'
            })
            
            # Start agent processor
            agent_cmd = [
                sys.executable, '-m', 'agent.processor'
            ]
            
            process = subprocess.Popen(
                agent_cmd,
                env=env,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it time to start
            await asyncio.sleep(3)
            
            if process.poll() is None:
                return process
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Agent process failed to start: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error starting agent processor: {e}")
            return None
    
    async def run_test_scenarios(self) -> Dict[str, Any]:
        """Run all test scenarios"""
        logger.info("Running test scenarios...")
        
        test_results = {}
        start_time = time.time()
        
        for scenario in self.test_scenarios:
            scenario_name = scenario['name']
            logger.info(f"Running scenario: {scenario_name}")
            
            try:
                result = await self._run_single_scenario(scenario)
                test_results[scenario_name] = result
                
                if result['passed']:
                    self.test_results['assertions_passed'] += 1
                    logger.info(f"✅ Scenario {scenario_name} PASSED")
                else:
                    self.test_results['assertions_failed'] += 1
                    logger.error(f"❌ Scenario {scenario_name} FAILED: {result.get('error', 'Unknown error')}")
                
                # Wait between scenarios
                await asyncio.sleep(2)
                
            except Exception as e:
                test_results[scenario_name] = {
                    'passed': False,
                    'error': str(e),
                    'transaction_sent': False,
                    'decision_received': False
                }
                self.test_results['assertions_failed'] += 1
                logger.error(f"❌ Scenario {scenario_name} FAILED with exception: {e}")
        
        self.test_results['test_duration'] = time.time() - start_time
        return test_results
    
    async def _run_single_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario"""
        scenario_name = scenario['name']
        transaction = scenario['transaction']
        
        result = {
            'passed': False,
            'transaction_sent': False,
            'decision_received': False,
            'decision_data': None,
            'assertions': {},
            'error': None
        }
        
        try:
            # Send transaction
            transaction_json = json.dumps(transaction, default=str)
            
            self.producer.produce(
                topic='financial-transactions',
                key=transaction['transaction_id'],
                value=transaction_json,
                callback=lambda err, msg: logger.info(f"Transaction sent: {msg.topic()}")
            )
            
            self.producer.flush(timeout=10)
            result['transaction_sent'] = True
            self.test_results['transactions_sent'] += 1
            
            logger.info(f"Sent transaction for scenario {scenario_name}")
            
            # Wait for and validate decision
            decision = await self._wait_for_decision(transaction['transaction_id'], timeout=30)
            
            if decision:
                result['decision_received'] = True
                result['decision_data'] = decision
                self.test_results['decisions_received'] += 1
                
                # Validate decision
                validation_result = await self._validate_decision(decision, scenario)
                result['assertions'] = validation_result
                result['passed'] = validation_result['all_passed']
                
            else:
                result['error'] = "No decision received within timeout"
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Error in scenario {scenario_name}: {e}")
        
        return result
    
    async def _wait_for_decision(self, transaction_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Wait for AI decision for a specific transaction"""
        consumer = self.consumers['decisions']
        start_time = time.time()
        
        logger.info(f"Waiting for decision for transaction {transaction_id}")
        
        while time.time() - start_time < timeout:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
            
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Consumer error: {msg.error()}")
                continue
            
            try:
                decision = json.loads(msg.value().decode('utf-8'))
                
                if decision.get('transaction_id') == transaction_id:
                    logger.info(f"Received decision for transaction {transaction_id}")
                    consumer.commit(msg)
                    return decision
                    
            except Exception as e:
                logger.error(f"Error parsing decision message: {e}")
        
        logger.warning(f"Timeout waiting for decision for transaction {transaction_id}")
        return None
    
    async def _validate_decision(self, decision: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Validate AI decision against expected results"""
        validations = {}
        
        # Validate decision structure
        validations['has_decision_id'] = 'decision_id' in decision
        validations['has_transaction_id'] = 'transaction_id' in decision
        validations['has_decision_type'] = 'decision_type' in decision
        validations['has_risk_level'] = 'risk_level' in decision
        validations['has_reasoning'] = 'reasoning' in decision
        validations['has_tool_calls'] = 'tool_calls_made' in decision
        
        # Validate expected risk level
        expected_risk = scenario.get('expected_risk_level')
        actual_risk = decision.get('risk_level')
        validations['risk_level_match'] = actual_risk == expected_risk
        
        if not validations['risk_level_match']:
            logger.warning(f"Risk level mismatch: expected {expected_risk}, got {actual_risk}")
        
        # Validate expected decision
        expected_decision = scenario.get('expected_decision')
        actual_decision = decision.get('decision_type')
        validations['decision_type_match'] = actual_decision == expected_decision
        
        if not validations['decision_type_match']:
            logger.warning(f"Decision type mismatch: expected {expected_decision}, got {actual_decision}")
        
        # Validate tool calls
        expected_tools = set(scenario.get('expected_tools', []))
        actual_tools = set(decision.get('tool_calls_made', []))
        
        validations['required_tools_called'] = expected_tools.issubset(actual_tools)
        validations['tool_calls_count'] = len(actual_tools)
        
        if not validations['required_tools_called']:
            missing_tools = expected_tools - actual_tools
            logger.warning(f"Missing expected tools: {missing_tools}")
        
        # Validate processing time
        processing_time = decision.get('processing_time_ms', 0)
        validations['reasonable_processing_time'] = 0 < processing_time < 30000  # Under 30 seconds
        
        # Validate confidence score
        confidence = decision.get('confidence_score', 0)
        validations['valid_confidence_score'] = 0 <= confidence <= 1
        
        # Overall validation
        validations['all_passed'] = all([
            validations['has_decision_id'],
            validations['has_transaction_id'],
            validations['has_decision_type'],
            validations['has_risk_level'],
            validations['has_reasoning'],
            validations['has_tool_calls'],
            validations['risk_level_match'],
            validations['decision_type_match'],
            validations['required_tools_called'],
            validations['reasonable_processing_time'],
            validations['valid_confidence_score']
        ])
        
        # Track tool calls validation
        if validations['required_tools_called']:
            self.test_results['tool_calls_validated'] += 1
        
        return validations
    
    async def verify_fraud_pattern_search(self) -> Dict[str, Any]:
        """Test fraud pattern search functionality"""
        logger.info("Testing fraud pattern search...")
        
        try:
            # Test with placeholder API key
            rag = FraudPatternRAG("test_api_key")
            
            # Test search queries
            test_queries = [
                "Multiple small transactions from same IP",
                "Large international wire transfer",
                "Card testing patterns",
                "Account takeover indicators"
            ]
            
            search_results = {}
            
            for query in test_queries:
                try:
                    result = await rag.search_fraud_patterns(query, n_results=3)
                    search_results[query] = {
                        'status': result.get('status'),
                        'total_results': result.get('total_results', 0),
                        'success': result.get('status') == 'success' and result.get('total_results', 0) > 0
                    }
                except Exception as e:
                    search_results[query] = {
                        'status': 'error',
                        'error': str(e),
                        'success': False
                    }
            
            overall_success = any(result['success'] for result in search_results.values())
            
            return {
                'overall_success': overall_success,
                'search_results': search_results,
                'collection_stats': rag.get_collection_stats()
            }
            
        except Exception as e:
            logger.error(f"Fraud pattern search test failed: {e}")
            return {
                'overall_success': False,
                'error': str(e)
            }
    
    async def cleanup(self):
        """Clean up test resources"""
        logger.info("Cleaning up test resources...")
        
        try:
            # Close consumers
            for name, consumer in self.consumers.items():
                consumer.close()
                logger.info(f"Closed {name} consumer")
            
            # Close producer
            if self.producer:
                self.producer.flush(timeout=10)
                logger.info("Closed producer")
            
            # Terminate processes
            for name, process in self.processes.items():
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                logger.info(f"Terminated {name} process")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def generate_test_report(self, test_results: Dict[str, Any], 
                           rag_test_results: Dict[str, Any]) -> str:
        """Generate comprehensive test report"""
        
        total_scenarios = len(self.test_scenarios)
        passed_scenarios = sum(1 for result in test_results.values() if result.get('passed', False))
        failed_scenarios = total_scenarios - passed_scenarios
        
        report = f"""
FRAUD DETECTION SYSTEM - END-TO-END TEST REPORT
{'=' * 60}

OVERALL RESULTS:
- Total Scenarios: {total_scenarios}
- Passed: {passed_scenarios}
- Failed: {failed_scenarios}
- Success Rate: {(passed_scenarios/total_scenarios)*100:.1f}%
- Test Duration: {self.test_results['test_duration']:.2f}s

PIPELINE METRICS:
- Transactions Sent: {self.test_results['transactions_sent']}
- Decisions Received: {self.test_results['decisions_received']}
- Tool Calls Validated: {self.test_results['tool_calls_validated']}
- Pipeline Success Rate: {(self.test_results['decisions_received']/max(self.test_results['transactions_sent'], 1))*100:.1f}%

SCENARIO DETAILS:
"""
        
        for scenario_name, result in test_results.items():
            status = "PASSED" if result.get('passed', False) else "FAILED"
            report += f"\n{scenario_name}: {status}"
            
            if result.get('decision_data'):
                decision = result['decision_data']
                report += f"""
  - Risk Level: {decision.get('risk_level', 'Unknown')}
  - Decision: {decision.get('decision_type', 'Unknown')}
  - Tools Used: {', '.join(decision.get('tool_calls_made', []))}
  - Processing Time: {decision.get('processing_time_ms', 0)}ms
"""
            
            if result.get('error'):
                report += f"  - Error: {result['error']}\n"
        
        # RAG system results
        report += f"""
RAG SYSTEM TEST:
- Overall Success: {'PASSED' if rag_test_results.get('overall_success', False) else 'FAILED'}
- Collection Stats: {rag_test_results.get('collection_stats', {})}
"""
        
        # Search results
        if 'search_results' in rag_test_results:
            report += "\nFRAUD PATTERN SEARCHES:\n"
            for query, result in rag_test_results['search_results'].items():
                status = "PASS" if result.get('success', False) else "FAIL"
                report += f"  {status} '{query}': {result.get('total_results', 0)} results\n"
        
        report += f"""
{'=' * 60}
Report generated at: {datetime.now().isoformat()}
"""
        
        return report


async def main():
    """Main test execution function"""
    print("Starting End-to-End Test Suite for Fraud Detection System")
    print("=" * 70)
    
    test_suite = E2ETestSuite()
    
    try:
        # Setup infrastructure
        print("📋 Setting up test infrastructure...")
        if not await test_suite.setup_infrastructure():
            print("❌ Infrastructure setup failed. Exiting.")
            return 1
        
        # Start services
        print("Starting fraud detection services...")
        services_status = await test_suite.start_services()
        
        if not services_status.get('agent', False):
            print("Failed to start required services. Exiting.")
            return 1
        
        # Run test scenarios
        print("Running test scenarios...")
        test_results = await test_suite.run_test_scenarios()
        
        # Test RAG system
        print("Testing RAG system...")
        rag_test_results = await test_suite.verify_fraud_pattern_search()
        
        # Generate and display report
        report = test_suite.generate_test_report(test_results, rag_test_results)
        print(report)
        
        # Save report to file
        with open('e2e_test_report.txt', 'w') as f:
            f.write(report)
        
        print("Test report saved to e2e_test_report.txt")
        
        # Determine exit code
        total_scenarios = len(test_suite.test_scenarios)
        passed_scenarios = sum(1 for result in test_results.values() if result.get('passed', False))
        
        if passed_scenarios == total_scenarios and rag_test_results.get('overall_success', False):
            print("All tests passed!")
            return 0
        else:
            print(f"{total_scenarios - passed_scenarios} tests failed.")
            return 1
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"Test suite failed with error: {e}")
        return 1
    finally:
        print("Cleaning up...")
        await test_suite.cleanup()


if __name__ == "__main__":
    # Run the test suite
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


# Pytest integration (only if pytest is available)
if PYTEST_AVAILABLE:
    class TestE2EFraudDetection:
        """Pytest class for E2E testing"""
        
        @pytest.fixture(scope="class")
        async def test_suite(self):
            """Setup test suite fixture"""
            suite = E2ETestSuite()
            await suite.setup_infrastructure()
            yield suite
            await suite.cleanup()
        
        @pytest.mark.asyncio
        async def test_infrastructure_setup(self, test_suite):
            """Test infrastructure setup"""
            assert await test_suite.setup_infrastructure()
        
        @pytest.mark.asyncio
        async def test_normal_transaction_flow(self, test_suite):
            """Test normal transaction processing"""
            await test_suite.start_services()
            
            normal_scenario = next(s for s in test_suite.test_scenarios if s['name'] == 'normal_transaction')
            result = await test_suite._run_single_scenario(normal_scenario)
            
            assert result['passed'], f"Normal transaction test failed: {result.get('error', 'Unknown error')}"
            assert result['transaction_sent']
            assert result['decision_received']
        
        @pytest.mark.asyncio
        async def test_high_risk_transaction_flow(self, test_suite):
            """Test high-risk transaction processing"""
            await test_suite.start_services()
            
            high_risk_scenario = next(s for s in test_suite.test_scenarios if s['name'] == 'suspicious_international')
            result = await test_suite._run_single_scenario(high_risk_scenario)
            
            assert result['passed'], f"High-risk transaction test failed: {result.get('error', 'Unknown error')}"
            assert result['decision_received']
            assert result['decision_data']['risk_level'] in ['HIGH', 'CRITICAL']
        
        @pytest.mark.asyncio
        async def test_rag_system(self, test_suite):
            """Test RAG fraud pattern search"""
            rag_results = await test_suite.verify_fraud_pattern_search()
            assert rag_results['overall_success'], "RAG system test failed"
        
        @pytest.mark.asyncio
        async def test_all_scenarios(self, test_suite):
            """Test all scenarios"""
            await test_suite.start_services()
            test_results = await test_suite.run_test_scenarios()
            
            total_scenarios = len(test_suite.test_scenarios)
            passed_scenarios = sum(1 for result in test_results.values() if result.get('passed', False))
            
            assert passed_scenarios == total_scenarios, f"Only {passed_scenarios}/{total_scenarios} scenarios passed"