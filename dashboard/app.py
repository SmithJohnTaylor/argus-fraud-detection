#!/usr/bin/env python3
"""
Real-Time Financial Transaction Monitoring Dashboard
Modern Streamlit dashboard with live streaming, agent reasoning, and analytics
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import deque, defaultdict
import queue

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from confluent_kafka import Consumer, KafkaError

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Financial Transaction Monitor",
    page_icon="●",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourcompany/fraud-detection',
        'Report a bug': "https://github.com/yourcompany/fraud-detection/issues",
        'About': "Real-time AI-powered fraud detection system"
    }
)

# Custom CSS for modern UI
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .metric-card p {
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    .alert-critical {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        border-left: 5px solid #c0392b;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .alert-high {
        background: linear-gradient(135deg, #ffa726 0%, #ff7043 100%);
        border-left: 5px solid #e65100;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .alert-medium {
        background: linear-gradient(135deg, #ffeb3b 0%, #ffc107 100%);
        border-left: 5px solid #ff8f00;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        color: #333;
    }
    
    .alert-low {
        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
        border-left: 5px solid #2e7d32;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .reasoning-box {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
    }
    
    .tool-call {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 4px;
    }
    
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)


class StreamingDataManager:
    """Manages real-time data streams for the dashboard"""
    
    def __init__(self):
        self.transactions = deque(maxlen=1000)
        self.decisions = deque(maxlen=500)
        self.alerts = deque(maxlen=200)
        self.metrics = {
            'total_transactions': 0,
            'total_alerts': 0,
            'avg_processing_time': 0,
            'alert_rate': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()
        
        # Time series data for charts
        self.transaction_volume = defaultdict(int)
        self.risk_scores_history = deque(maxlen=100)
        self.processing_times = deque(maxlen=100)
        
        # Real-time streaming queues
        self.transaction_queue = queue.Queue(maxsize=100)
        self.decision_queue = queue.Queue(maxsize=100)
        self.reasoning_queue = queue.Queue(maxsize=50)
    
    def add_transaction(self, transaction: Dict[str, Any]):
        """Add new transaction to the stream"""
        with self.lock:
            self.transactions.append(transaction)
            self.metrics['total_transactions'] += 1
            
            # Update time series
            timestamp = transaction.get('timestamp', datetime.now().isoformat())
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour_key = dt.strftime('%H:%M')
                self.transaction_volume[hour_key] += 1
            except:
                pass
            
            # Add to real-time queue
            try:
                self.transaction_queue.put_nowait(transaction)
            except queue.Full:
                pass
    
    def add_decision(self, decision: Dict[str, Any]):
        """Add AI decision to the stream"""
        with self.lock:
            self.decisions.append(decision)
            
            # Update metrics
            processing_time = decision.get('processing_time_ms', 0)
            if processing_time > 0:
                self.processing_times.append(processing_time)
                if self.processing_times:
                    self.metrics['avg_processing_time'] = sum(self.processing_times) / len(self.processing_times)
            
            # Track risk scores
            risk_score = decision.get('risk_assessment', {}).get('overall_risk_score', 0)
            if risk_score:
                self.risk_scores_history.append(risk_score)
            
            # Add to queue
            try:
                self.decision_queue.put_nowait(decision)
            except queue.Full:
                pass
    
    def add_alert(self, alert: Dict[str, Any]):
        """Add alert to the stream"""
        with self.lock:
            self.alerts.append(alert)
            self.metrics['total_alerts'] += 1
            
            # Calculate alert rate
            if self.metrics['total_transactions'] > 0:
                self.metrics['alert_rate'] = (self.metrics['total_alerts'] / self.metrics['total_transactions']) * 100
    
    def add_reasoning_step(self, reasoning: Dict[str, Any]):
        """Add reasoning step for real-time display"""
        try:
            self.reasoning_queue.put_nowait(reasoning)
        except queue.Full:
            pass
    
    def get_recent_transactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        with self.lock:
            return list(self.transactions)[-limit:]
    
    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent AI decisions"""
        with self.lock:
            return list(self.decisions)[-limit:]
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        with self.lock:
            return list(self.alerts)[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self.lock:
            uptime = time.time() - self.metrics['start_time']
            rate = self.metrics['total_transactions'] / (uptime / 60) if uptime > 0 else 0
            
            return {
                **self.metrics,
                'uptime_minutes': uptime / 60,
                'transaction_rate_per_minute': rate
            }


class KafkaStreamConsumer:
    """Kafka consumer for real-time data streaming"""
    
    def __init__(self, data_manager: StreamingDataManager):
        self.data_manager = data_manager
        self.running = False
        self.consumers = {}
        
        # Confluent Cloud Kafka configuration (simplified)
        self.kafka_config = {
            'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
            'security.protocol': 'SASL_SSL',
            'sasl.mechanism': 'PLAIN',
            'sasl.username': os.getenv('CONFLUENT_API_KEY'),
            'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
            'group.id': 'dashboard-consumer-group',
            'auto.offset.reset': 'earliest'
        }
        
        # Validate Confluent Cloud configuration
        required_keys = ['bootstrap.servers', 'sasl.username', 'sasl.password']
        for key in required_keys:
            if not self.kafka_config.get(key):
                logger.error(f"Missing required Confluent Cloud configuration: {key}")
                raise ValueError(f"Dashboard requires Confluent Cloud configuration: {key}")
    
    def start_consumers(self):
        """Start Kafka consumers in background threads"""
        if self.running:
            print("🔵 Dashboard: Consumers already running")
            return
        
        self.running = True
        
        # Consumer for transactions
        tx_thread = threading.Thread(
            target=self._consume_transactions,
            daemon=True
        )
        tx_thread.start()
        
        # Consumer for AI decisions
        decision_thread = threading.Thread(
            target=self._consume_decisions,
            daemon=True
        )
        decision_thread.start()
        logger.info("Started Kafka consumers")
    
    def stop_consumers(self):
        """Stop all consumers"""
        self.running = False
        for consumer in self.consumers.values():
            consumer.close()
        logger.info("Stopped Kafka consumers")
    
    def _consume_transactions(self):
        """Consume transactions from Kafka"""
        try:
            print("🔵 Starting transaction consumer...")
            import uuid
            consumer = Consumer({
                **self.kafka_config,
                'group.id': f'dashboard-transactions-{uuid.uuid4().hex[:8]}',
                'auto.offset.reset': 'latest'  # Start from newest messages
            })
            topic = os.getenv('KAFKA_TOPIC_TRANSACTIONS', 'financial-transactions')
            consumer.subscribe([topic])
            self.consumers['transactions'] = consumer
            print(f"🔵 Transaction consumer subscribed to {topic}")
            
            while self.running:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Transaction consumer error: {msg.error()}")
                    continue
                
                try:
                    transaction = json.loads(msg.value().decode('utf-8'))
                    self.data_manager.add_transaction(transaction)
                    # Transaction added successfully
                except Exception as e:
                    logger.error(f"Error processing transaction: {e}")
                    print(f"🔴 Dashboard: Transaction processing error: {e}")
        
        except Exception as e:
            logger.error(f"Transaction consumer error: {e}")
        finally:
            if 'transactions' in self.consumers:
                self.consumers['transactions'].close()
    
    def _consume_decisions(self):
        """Consume AI decisions from Kafka"""
        try:
            consumer = Consumer({
                **self.kafka_config,
                'group.id': 'dashboard-decisions-group'
            })
            consumer.subscribe([os.getenv('KAFKA_TOPIC_DECISIONS', 'ai-decisions')])
            self.consumers['decisions'] = consumer
            
            while self.running:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.error(f"Decision consumer error: {msg.error()}")
                    continue
                
                try:
                    decision = json.loads(msg.value().decode('utf-8'))
                    self.data_manager.add_decision(decision)
                    # Decision added successfully
                    
                    # Generate mock alert if high risk
                    risk_level = decision.get('risk_level', 'LOW')
                    if risk_level in ['HIGH', 'CRITICAL']:
                        alert = self._create_alert_from_decision(decision)
                        self.data_manager.add_alert(alert)
                        print(f"🟡 Dashboard: Generated alert for {risk_level} risk decision")
                    
                    # Add reasoning steps
                    self._add_reasoning_steps(decision)
                    
                except Exception as e:
                    logger.error(f"Error processing decision: {e}")
        
        except Exception as e:
            logger.error(f"Decision consumer error: {e}")
        finally:
            if 'decisions' in self.consumers:
                self.consumers['decisions'].close()
    
    def _create_alert_from_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert from high-risk decision"""
        return {
            'alert_id': f"ALT_{decision.get('decision_id', 'unknown')[:8]}",
            'transaction_id': decision.get('transaction_id'),
            'alert_type': 'FRAUD_DETECTION',
            'priority': 'P1_CRITICAL' if decision.get('risk_level') == 'CRITICAL' else 'P2_HIGH',
            'severity': decision.get('risk_level'),
            'title': f"{decision.get('risk_level')} Risk Transaction Detected",
            'description': decision.get('reasoning', 'High-risk transaction detected by AI'),
            'created_at': datetime.now().isoformat(),
            'status': 'ACTIVE'
        }
    
    def _add_reasoning_steps(self, decision: Dict[str, Any]):
        """Add reasoning steps from decision"""
        tool_calls = decision.get('tool_calls_made', [])
        
        for tool in tool_calls:
            reasoning = {
                'timestamp': datetime.now().isoformat(),
                'step_type': 'tool_call',
                'tool_name': tool,
                'transaction_id': decision.get('transaction_id'),
                'status': 'completed'
            }
            self.data_manager.add_reasoning_step(reasoning)


def create_mock_data():
    """Create mock data for development/testing"""
    mock_transactions = []
    mock_decisions = []
    mock_alerts = []
    
    # Generate mock transactions
    for i in range(50):
        transaction = {
            'transaction_id': f'TXN_{i:06d}',
            'customer_id': f'CUST_{random.randint(1000, 9999)}',
            'amount': round(random.uniform(10, 5000), 2),
            'merchant_id': random.choice(['AMAZON', 'STARBUCKS', 'SHELL', 'WALMART', 'UNKNOWN_MERCHANT']),
            'location': {
                'city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston']),
                'country': 'USA'
            },
            'timestamp': (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat(),
            'payment_method': random.choice(['CREDIT_CARD', 'DEBIT_CARD', 'WIRE_TRANSFER'])
        }
        mock_transactions.append(transaction)
        
        # Create corresponding decision
        risk_level = random.choices(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'], weights=[0.6, 0.25, 0.1, 0.05])[0]
        decision = {
            'decision_id': f'DEC_{i:06d}',
            'transaction_id': transaction['transaction_id'],
            'decision_type': random.choice(['APPROVE', 'DECLINE', 'MANUAL_REVIEW']),
            'risk_level': risk_level,
            'confidence_score': round(random.uniform(0.3, 0.95), 3),
            'reasoning': f"Transaction analysis indicates {risk_level.lower()} risk based on amount and merchant patterns.",
            'tool_calls_made': random.sample(['check_transaction_history', 'calculate_risk_score', 'check_compliance_rules'], k=random.randint(1, 3)),
            'processing_time_ms': random.randint(500, 3000),
            'timestamp': transaction['timestamp']
        }
        mock_decisions.append(decision)
        
        # Create alert for high-risk decisions
        if risk_level in ['HIGH', 'CRITICAL']:
            alert = {
                'alert_id': f'ALT_{i:04d}',
                'transaction_id': transaction['transaction_id'],
                'alert_type': 'FRAUD_DETECTION',
                'priority': 'P1_CRITICAL' if risk_level == 'CRITICAL' else 'P2_HIGH',
                'severity': risk_level,
                'title': f'{risk_level} Risk Transaction',
                'description': f'Suspicious {transaction["merchant_id"]} transaction',
                'created_at': transaction['timestamp'],
                'status': 'ACTIVE'
            }
            mock_alerts.append(alert)
    
    return mock_transactions, mock_decisions, mock_alerts


# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = StreamingDataManager()
    
if 'kafka_consumer' not in st.session_state:
    try:
        st.session_state.kafka_consumer = KafkaStreamConsumer(st.session_state.data_manager)
    except Exception as e:
        st.error(f"Failed to initialize Kafka consumer: {e}")
        st.session_state.kafka_consumer = None

# Mock data loading disabled - dashboard will show live Kafka data only
if 'mock_data_loaded' not in st.session_state:
    st.session_state.mock_data_loaded = True


def render_header():
    """Render dashboard header"""
    st.title("Real-Time Financial Transaction Monitor")
    st.markdown("### AI-Powered Fraud Detection Dashboard")
    
    # Simplified layout - make button more prominent
    st.markdown("### Controls")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown("**Status:** Live Monitoring Active")
    
    with col2:
        # Check if consumers are already running
        if 'consumers_running' not in st.session_state:
            st.session_state.consumers_running = False
            
        if not st.session_state.consumers_running:
            if st.button("Start Kafka Streams", type="primary"):
                if st.session_state.kafka_consumer:
                    st.session_state.kafka_consumer.start_consumers()
                    st.session_state.consumers_running = True
                    # Don't show success message here - it causes flashing
                else:
                    st.error("Kafka consumer not available")
        else:
            st.success("Kafka Streams Running")
    
    with col3:
        if st.session_state.get('consumers_running', False):
            if st.button("Stop Streams"):
                if st.session_state.kafka_consumer:
                    st.session_state.kafka_consumer.stop_consumers()
                    st.session_state.consumers_running = False
                else:
                    st.error("Kafka consumer not available")
    
    with col4:
        if st.button("Refresh Data"):
            st.rerun()


def render_metrics_dashboard():
    """Render key metrics dashboard"""
    st.markdown("## Key Metrics")
    
    metrics = st.session_state.data_manager.get_metrics()
    
    # Debug info (optional)
    if st.checkbox("Show Debug Info"):
        with st.expander("Debug Info"):
            st.write("Data Manager Metrics:", metrics)
            st.write("Transactions in queue:", len(st.session_state.data_manager.transactions))
            st.write("Decisions in queue:", len(st.session_state.data_manager.decisions))
            st.write("Alerts in queue:", len(st.session_state.data_manager.alerts))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['total_transactions']:,}</h3>
            <p>Total Transactions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['total_alerts']}</h3>
            <p>Alerts Generated</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['avg_processing_time']:.0f}ms</h3>
            <p>Avg Processing Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{metrics['alert_rate']:.1f}%</h3>
            <p>Alert Rate</p>
        </div>
        """, unsafe_allow_html=True)


def render_transaction_volume_chart():
    """Render transaction volume over time chart"""
    st.markdown("## Transaction Volume Over Time")
    
    # Get transaction volume data
    data_manager = st.session_state.data_manager
    volume_data = dict(data_manager.transaction_volume)
    
    if volume_data:
        # Create time series data
        times = list(volume_data.keys())
        volumes = list(volume_data.values())
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=times,
            y=volumes,
            mode='lines+markers',
            name='Transaction Volume',
            line=dict(color='#667eea', width=3),
            marker=dict(size=6, color='#764ba2'),
            fill='tonexty',
            fillcolor='rgba(102, 126, 234, 0.1)'
        ))
        
        fig.update_layout(
            title="Transaction Volume by Hour",
            xaxis_title="Time (Hour:Minute)",
            yaxis_title="Number of Transactions",
            height=400,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No transaction volume data available yet.")


def render_risk_score_distribution():
    """Render risk score distribution chart"""
    st.markdown("## ⚠️ Risk Score Distribution")
    
    decisions = st.session_state.data_manager.get_recent_decisions(100)
    
    if decisions:
        risk_levels = [d.get('risk_level', 'UNKNOWN') for d in decisions]
        risk_counts = pd.Series(risk_levels).value_counts()
        
        # Color mapping for risk levels
        colors = {
            'LOW': '#4caf50',
            'MEDIUM': '#ffeb3b', 
            'HIGH': '#ff9800',
            'CRITICAL': '#f44336',
            'UNKNOWN': '#9e9e9e'
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=risk_counts.index,
                y=risk_counts.values,
                marker_color=[colors.get(level, '#9e9e9e') for level in risk_counts.index],
                text=risk_counts.values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Risk Level Distribution (Last 100 Decisions)",
            xaxis_title="Risk Level",
            yaxis_title="Count",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk score timeline
        st.markdown("### Risk Score Timeline")
        
        risk_scores = [d.get('confidence_score', 0) for d in decisions[-50:]]
        timestamps = [d.get('timestamp', datetime.now().isoformat()) for d in decisions[-50:]]
        
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=list(range(len(risk_scores))),
            y=risk_scores,
            mode='lines+markers',
            name='Confidence Score',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=5)
        ))
        
        fig_timeline.update_layout(
            title="Decision Confidence Scores (Last 50)",
            xaxis_title="Decision Number",
            yaxis_title="Confidence Score",
            height=300,
            template="plotly_white",
            showlegend=False
        )
        
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.info("No risk score data available yet.")


def render_tool_usage_analysis():
    """Render tool usage analysis"""
    st.markdown("## 🔧 AI Tool Usage Analysis")
    
    decisions = st.session_state.data_manager.get_recent_decisions(100)
    
    if decisions:
        # Count tool usage
        tool_usage = defaultdict(int)
        for decision in decisions:
            tools = decision.get('tool_calls_made', [])
            for tool in tools:
                tool_usage[tool] += 1
        
        if tool_usage:
            tools = list(tool_usage.keys())
            counts = list(tool_usage.values())
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=tools,
                    values=counts,
                    hole=0.4,
                    marker_colors=['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe']
                )
            ])
            
            fig.update_layout(
                title="Tool Usage Distribution",
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Processing time by tool
            st.markdown("### Processing Time Analysis")
            
            processing_times = [d.get('processing_time_ms', 0) for d in decisions[-20:]]
            
            fig_time = go.Figure()
            fig_time.add_trace(go.Histogram(
                x=processing_times,
                nbinsx=10,
                marker_color='rgba(102, 126, 234, 0.7)',
                opacity=0.7
            ))
            
            fig_time.update_layout(
                title="Processing Time Distribution (ms)",
                xaxis_title="Processing Time (ms)",
                yaxis_title="Frequency",
                height=300,
                template="plotly_white"
            )
            
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No tool usage data available yet.")
    else:
        st.info("No decision data available yet.")


def render_live_transaction_stream():
    """Render live transaction stream"""
    st.markdown("## Live Transaction Stream")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh every 2 seconds", value=True)
    
    if auto_refresh:
        time.sleep(2)
        st.rerun()
    
    transactions = st.session_state.data_manager.get_recent_transactions(20)
    
    if transactions:
        # Create DataFrame for display
        display_data = []
        for tx in reversed(transactions[-10:]):  # Show last 10
            display_data.append({
                'Time': tx.get('timestamp', '')[:19].replace('T', ' '),
                'Transaction ID': tx.get('transaction_id', '')[:12] + '...',
                'Amount': f"${tx.get('amount', 0):,.2f}",
                'Merchant': tx.get('merchant_id', ''),
                'Location': f"{tx.get('location', {}).get('city', 'Unknown')}, {tx.get('location', {}).get('country', 'Unknown')}",
                'Payment Method': tx.get('payment_method', '')
            })
        
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True, height=350)
    else:
        st.info("No transactions in stream yet. Start the producer to see live data.")


def render_agent_reasoning():
    """Render real-time agent reasoning"""
    st.markdown("## AI Agent Reasoning (Real-time)")
    
    reasoning_container = st.container()
    
    # Get recent reasoning steps
    try:
        reasoning_steps = []
        while not st.session_state.data_manager.reasoning_queue.empty():
            step = st.session_state.data_manager.reasoning_queue.get_nowait()
            reasoning_steps.append(step)
    except queue.Empty:
        reasoning_steps = []
    
    # Show recent decisions with reasoning
    decisions = st.session_state.data_manager.get_recent_decisions(5)
    
    with reasoning_container:
        if decisions:
            for decision in reversed(decisions[-3:]):  # Show last 3
                transaction_id = decision.get('transaction_id', 'Unknown')
                risk_level = decision.get('risk_level', 'UNKNOWN')
                reasoning = decision.get('reasoning', 'No reasoning provided')
                tools_used = decision.get('tool_calls_made', [])
                
                # Color code by risk level
                if risk_level == 'CRITICAL':
                    box_class = 'alert-critical'
                elif risk_level == 'HIGH':
                    box_class = 'alert-high'
                elif risk_level == 'MEDIUM':
                    box_class = 'alert-medium'
                else:
                    box_class = 'alert-low'
                
                st.markdown(f"""
                <div class="{box_class}">
                    <h4>Transaction: {transaction_id}</h4>
                    <p><strong>Risk Level:</strong> {risk_level}</p>
                    <p><strong>Decision:</strong> {decision.get('decision_type', 'Unknown')}</p>
                    <div class="reasoning-box">
                        <strong>AI Reasoning:</strong><br>
                        {reasoning}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show tool calls
                if tools_used:
                    st.markdown("**Tools Used:**")
                    for tool in tools_used:
                        st.markdown(f"""
                        <div class="tool-call">
                            🔧 {tool}
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
        else:
            st.info("No AI reasoning available yet. Process some transactions to see agent decisions.")


def render_alerts_panel():
    """Render alerts panel with priority levels"""
    st.markdown("## Recent Alerts")
    
    alerts = st.session_state.data_manager.get_recent_alerts(15)
    
    if alerts:
        # Priority filter
        priority_filter = st.selectbox(
            "Filter by Priority",
            ["All", "P1_CRITICAL", "P2_HIGH", "P3_MEDIUM", "P4_LOW"],
            index=0
        )
        
        filtered_alerts = alerts
        if priority_filter != "All":
            filtered_alerts = [a for a in alerts if a.get('priority') == priority_filter]
        
        # Display alerts
        for alert in reversed(filtered_alerts[-10:]):  # Show last 10
            priority = alert.get('priority', 'P4_LOW')
            severity = alert.get('severity', 'LOW')
            title = alert.get('title', 'Alert')
            description = alert.get('description', 'No description')
            created_at = alert.get('created_at', '')[:19].replace('T', ' ')
            
            # Determine CSS class based on priority/severity
            if priority == 'P1_CRITICAL' or severity == 'CRITICAL':
                alert_class = 'alert-critical'
                icon = '🔴'
            elif priority == 'P2_HIGH' or severity == 'HIGH':
                alert_class = 'alert-high'
                icon = 'HIGH'
            elif priority == 'P3_MEDIUM' or severity == 'MEDIUM':
                alert_class = 'alert-medium'
                icon = 'MED'
            else:
                alert_class = 'alert-low'
                icon = 'LOW'
            
            st.markdown(f"""
            <div class="{alert_class}">
                <h4>{icon} {title}</h4>
                <p><strong>Priority:</strong> {priority} | <strong>Severity:</strong> {severity}</p>
                <p><strong>Time:</strong> {created_at}</p>
                <p><strong>Transaction:</strong> {alert.get('transaction_id', 'Unknown')}</p>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Alert statistics
        st.markdown("### Alert Statistics")
        
        alert_priorities = [a.get('priority', 'P4_LOW') for a in alerts]
        priority_counts = pd.Series(alert_priorities).value_counts()
        
        fig = go.Figure(data=[
            go.Bar(
                x=priority_counts.index,
                y=priority_counts.values,
                marker_color=['#f44336', '#ff9800', '#ffeb3b', '#4caf50'][:len(priority_counts)],
                text=priority_counts.values,
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Alert Distribution by Priority",
            xaxis_title="Priority Level",
            yaxis_title="Count",
            height=300,
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("No alerts generated yet.")


def render_sidebar():
    """Render sidebar with controls and settings"""
    with st.sidebar:
        st.markdown("## Controls")
        
        # System status
        st.markdown("### System Status")
        st.markdown("**Dashboard:** Online")
        st.markdown("**Kafka Streams:** Demo Mode")
        st.markdown("**AI Agent:** Ready")
        
        # Show current AI model
        current_model = os.getenv('TOGETHER_MODEL', 'mistralai/Mixtral-8x7B-Instruct-v0.1')
        model_name = current_model.split('/')[-1] if '/' in current_model else current_model
        st.markdown(f"**AI Model:** {model_name}")
        
        st.markdown("---")
        
        # Refresh controls
        st.markdown("### Refresh Settings")
        auto_refresh_global = st.checkbox("Global Auto-refresh", value=False)
        refresh_interval = st.slider("Refresh Interval (seconds)", 1, 30, 5)
        
        # Note: Auto-refresh disabled to prevent infinite loops
        if auto_refresh_global:
            st.info(f"Auto-refresh every {refresh_interval}s (disabled for now)")
            # TODO: Implement proper auto-refresh without blocking
        
        st.markdown("---")
        
        # Data controls
        st.markdown("### Data Controls")
        
        if st.button("Clear All Data"):
            st.session_state.data_manager = StreamingDataManager()
            st.success("Data cleared!")
            st.rerun()
        
        if st.button("Load Mock Data"):
            mock_transactions, mock_decisions, mock_alerts = create_mock_data()
            
            for tx in mock_transactions:
                st.session_state.data_manager.add_transaction(tx)
            
            for decision in mock_decisions:
                st.session_state.data_manager.add_decision(decision)
            
            for alert in mock_alerts:
                st.session_state.data_manager.add_alert(alert)
            
            st.success("Mock data loaded!")
            st.rerun()
        
        st.markdown("---")
        
        # Statistics
        st.markdown("### Quick Stats")
        metrics = st.session_state.data_manager.get_metrics()
        st.metric("Uptime", f"{metrics['uptime_minutes']:.1f} min")
        st.metric("TX Rate", f"{metrics.get('transaction_rate_per_minute', 0):.1f}/min")
        
        st.markdown("---")
        
        # Help
        st.markdown("### Help")
        st.markdown("[Documentation](https://github.com/yourcompany/fraud-detection)")
        st.markdown("[Report Issues](https://github.com/yourcompany/fraud-detection/issues)")


def main():
    """Main dashboard application"""
    render_sidebar()
    render_header()
    
    st.markdown("---")
    
    # Main dashboard layout
    render_metrics_dashboard()
    
    st.markdown("---")
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        render_transaction_volume_chart()
    
    with col2:
        render_risk_score_distribution()
    
    st.markdown("---")
    
    # Tool usage analysis
    render_tool_usage_analysis()
    
    st.markdown("---")
    
    # Live data row
    col1, col2 = st.columns([3, 2])
    
    with col1:
        render_live_transaction_stream()
    
    with col2:
        render_alerts_panel()
    
    st.markdown("---")
    
    # Agent reasoning (full width)
    render_agent_reasoning()


if __name__ == "__main__":
    main()