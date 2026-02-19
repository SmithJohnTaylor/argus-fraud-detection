#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Component for Fraud Pattern Knowledge
Uses ChromaDB vector store with Together AI embeddings for fraud pattern retrieval
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

import aiohttp
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class FraudPatternDocument:
    id: str
    title: str
    pattern_type: str
    severity: str
    description: str
    indicators: List[str]
    detection_methods: List[str]
    case_studies: List[Dict[str, Any]]
    prevention_measures: List[str]
    regulatory_notes: str
    tags: List[str]
    created_at: str


class TogetherAIEmbeddingFunction:
    """Custom embedding function using Together AI API"""
    
    def __init__(self, api_key: str, model_name: str = "togethercomputer/m2-bert-80M-8k-retrieval"):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = "https://api.together.xyz/v1"
        
    async def __call__(self, input_texts: List[str]) -> List[List[float]]:
        """Generate embeddings for input texts"""
        
        if not input_texts:
            return []
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.model_name,
                    "input": input_texts
                }
                
                async with session.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Embedding API error {response.status}: {error_text}")
                        # Fallback to dummy embeddings for development
                        return [[0.0] * 768 for _ in input_texts]
                    
                    result = await response.json()
                    embeddings = [item["embedding"] for item in result["data"]]
                    
                    logger.debug(f"Generated embeddings for {len(input_texts)} texts")
                    return embeddings
                    
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Fallback to dummy embeddings
            return [[0.0] * 768 for _ in input_texts]
    
    def __call_sync__(self, input_texts: List[str]) -> List[List[float]]:
        """Synchronous wrapper for embedding generation"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self(input_texts))
        finally:
            loop.close()


class FraudPatternRAG:
    """RAG system for fraud pattern knowledge retrieval"""
    
    def __init__(self, api_key: str, persist_directory: str = "./chroma_db"):
        self.api_key = api_key
        self.persist_directory = persist_directory
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding function
        self.embedding_function = TogetherAIEmbeddingFunction(api_key)
        
        # Get or create collection
        self.collection_name = "fraud_patterns"
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded existing collection '{self.collection_name}'")
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Fraud pattern knowledge base"}
            )
            logger.info(f"Created new collection '{self.collection_name}'")
        
        # Initialize with fraud patterns if collection is empty
        if self.collection.count() == 0:
            self._initialize_fraud_patterns()
    
    def _initialize_fraud_patterns(self):
        """Initialize the vector store with fraud pattern documents"""
        logger.info("Initializing fraud pattern knowledge base...")
        
        fraud_patterns = self._get_fraud_pattern_documents()
        
        # Prepare documents for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for pattern in fraud_patterns:
            # Create searchable document text
            doc_text = self._create_searchable_text(pattern)
            documents.append(doc_text)
            
            # Create metadata
            metadata = {
                "title": pattern.title,
                "pattern_type": pattern.pattern_type,
                "severity": pattern.severity,
                "tags": ",".join(pattern.tags),
                "created_at": pattern.created_at
            }
            metadatas.append(metadata)
            ids.append(pattern.id)
        
        # Add to collection (sync call)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Generate embeddings
            embeddings = loop.run_until_complete(
                self.embedding_function(documents)
            )
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Added {len(fraud_patterns)} fraud patterns to knowledge base")
            
        finally:
            loop.close()
    
    def _create_searchable_text(self, pattern: FraudPatternDocument) -> str:
        """Create searchable text from fraud pattern document"""
        
        text_parts = [
            f"Title: {pattern.title}",
            f"Pattern Type: {pattern.pattern_type}",
            f"Severity: {pattern.severity}",
            f"Description: {pattern.description}",
            f"Indicators: {'; '.join(pattern.indicators)}",
            f"Detection Methods: {'; '.join(pattern.detection_methods)}",
            f"Prevention Measures: {'; '.join(pattern.prevention_measures)}",
            f"Regulatory Notes: {pattern.regulatory_notes}",
            f"Tags: {', '.join(pattern.tags)}"
        ]
        
        # Add case studies
        for i, case_study in enumerate(pattern.case_studies):
            text_parts.append(f"Case Study {i+1}: {case_study.get('description', '')}")
        
        return "\n".join(text_parts)
    
    async def search_fraud_patterns(self, query: str, n_results: int = 5, 
                                  filter_criteria: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Search fraud patterns using semantic similarity
        
        Args:
            query: Search query describing fraud indicators or patterns
            n_results: Number of results to return
            filter_criteria: Optional filters (pattern_type, severity, etc.)
            
        Returns:
            Structured search results with relevant fraud patterns
        """
        logger.info(f"Searching fraud patterns for query: '{query}'")
        
        try:
            # Generate query embedding
            query_embedding = await self.embedding_function([query])
            
            # Prepare where filter
            where_filter = {}
            if filter_criteria:
                for key, value in filter_criteria.items():
                    if key in ["pattern_type", "severity"]:
                        where_filter[key] = value
                    elif key == "tags" and isinstance(value, str):
                        # Simple tag filtering (contains)
                        where_filter["tags"] = {"$contains": value}
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, 20),  # Cap at 20 results
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process and structure results
            structured_results = []
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0], 
                results["distances"][0]
            )):
                
                # Calculate similarity score (1 - distance for cosine distance)
                similarity_score = max(0, 1 - distance)
                
                result_item = {
                    "rank": i + 1,
                    "similarity_score": round(similarity_score, 3),
                    "title": metadata["title"],
                    "pattern_type": metadata["pattern_type"],
                    "severity": metadata["severity"],
                    "tags": metadata["tags"].split(",") if metadata["tags"] else [],
                    "content_preview": doc[:300] + "..." if len(doc) > 300 else doc,
                    "full_content": doc
                }
                
                structured_results.append(result_item)
            
            search_result = {
                "status": "success",
                "query": query,
                "total_results": len(structured_results),
                "results": structured_results,
                "search_metadata": {
                    "collection_size": self.collection.count(),
                    "search_time": "async",
                    "filter_applied": filter_criteria is not None,
                    "embedding_model": self.embedding_function.model_name
                }
            }
            
            logger.info(f"Found {len(structured_results)} relevant fraud patterns")
            return search_result
            
        except Exception as e:
            logger.error(f"Error searching fraud patterns: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "query": query,
                "results": []
            }
    
    def _get_fraud_pattern_documents(self) -> List[FraudPatternDocument]:
        """Generate comprehensive fraud pattern documents"""
        
        patterns = [
            FraudPatternDocument(
                id="fp_001",
                title="Credit Card Testing (Card Testing)",
                pattern_type="CARD_FRAUD",
                severity="HIGH",
                description="Fraudsters test stolen card numbers by making small purchases to verify if cards are active before conducting larger fraudulent transactions.",
                indicators=[
                    "Multiple small transactions ($1-$10) in short time period",
                    "Sequential card number patterns",
                    "High decline rate followed by successful small transactions",
                    "Transactions from same IP/device with different cards",
                    "Testing on low-value digital goods or donations"
                ],
                detection_methods=[
                    "Velocity monitoring for small transactions",
                    "Device fingerprinting across multiple cards", 
                    "Pattern recognition for sequential card testing",
                    "Decline rate analysis by merchant/location",
                    "Time-based clustering of similar transactions"
                ],
                case_studies=[
                    {
                        "description": "E-commerce site experienced 500+ $1 transactions in 2 hours from single IP",
                        "outcome": "Blocked IP range, prevented $50K in fraudulent purchases",
                        "indicators_present": ["velocity", "small_amounts", "single_IP"]
                    },
                    {
                        "description": "Charity donation platform used for card testing with $5 donations",
                        "outcome": "Implemented CAPTCHA and velocity limits",
                        "indicators_present": ["donation_abuse", "velocity", "pattern_recognition"]
                    }
                ],
                prevention_measures=[
                    "Implement velocity limits for small transactions",
                    "Use device fingerprinting and behavioral analysis",
                    "Implement CAPTCHA for high-risk transactions",
                    "Monitor and block suspicious IP ranges",
                    "Set minimum transaction amounts for certain merchants"
                ],
                regulatory_notes="Card testing may violate PCI DSS requirements and should be reported to card networks.",
                tags=["card_testing", "velocity", "small_transactions", "e_commerce", "validation_fraud"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_002", 
                title="Account Takeover (ATO)",
                pattern_type="ACCOUNT_FRAUD",
                severity="CRITICAL",
                description="Fraudsters gain unauthorized access to legitimate customer accounts through credential theft, social engineering, or technical exploits.",
                indicators=[
                    "Login from unusual geographic location",
                    "Multiple failed login attempts followed by success",
                    "Immediate changes to account information after login",
                    "Large transactions shortly after account access",
                    "Use of different devices/browsers than historical pattern"
                ],
                detection_methods=[
                    "Geographic velocity analysis (impossible travel)",
                    "Device and browser fingerprint analysis",
                    "Behavioral biometrics (typing patterns, mouse movements)",
                    "Account modification velocity monitoring",
                    "Transaction pattern deviation analysis"
                ],
                case_studies=[
                    {
                        "description": "Customer account accessed from Russia 2 hours after last US login",
                        "outcome": "Account frozen, customer contacted, password reset required",
                        "indicators_present": ["impossible_travel", "geographic_anomaly"]
                    },
                    {
                        "description": "Account showed 50 failed logins, then successful login with immediate $5K wire transfer",
                        "outcome": "Transaction blocked, account secured, credentials reset",
                        "indicators_present": ["brute_force", "immediate_large_transaction"]
                    }
                ],
                prevention_measures=[
                    "Implement multi-factor authentication (MFA)",
                    "Monitor login patterns and geographic locations",
                    "Use device registration and recognition",
                    "Implement step-up authentication for high-risk activities",
                    "Regular security awareness training for customers"
                ],
                regulatory_notes="ATO incidents may require customer notification under data breach laws and regulatory reporting.",
                tags=["account_takeover", "credential_theft", "geographic_anomaly", "MFA", "authentication"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_003",
                title="Money Laundering - Layering Stage",
                pattern_type="MONEY_LAUNDERING", 
                severity="CRITICAL",
                description="Complex series of transactions designed to obscure the source of illicit funds through multiple accounts and jurisdictions.",
                indicators=[
                    "Rapid movement of funds between multiple accounts",
                    "Round-number transfers with no clear business purpose",
                    "International wire transfers to high-risk jurisdictions",
                    "Transactions structured just below reporting thresholds",
                    "Use of multiple payment methods and currencies"
                ],
                detection_methods=[
                    "Network analysis of fund flows",
                    "Pattern recognition for structuring behavior",
                    "Geographic risk assessment",
                    "Velocity and frequency analysis",
                    "Cross-account relationship mapping"
                ],
                case_studies=[
                    {
                        "description": "Customer made 15 transfers of $9,900 each across different accounts in 1 week",
                        "outcome": "SAR filed, accounts monitored, eventually frozen",
                        "indicators_present": ["structuring", "velocity", "round_numbers"]
                    },
                    {
                        "description": "Complex web of transfers through 8 countries within 48 hours",
                        "outcome": "International cooperation, funds seized",
                        "indicators_present": ["international_layering", "rapid_movement", "complex_network"]
                    }
                ],
                prevention_measures=[
                    "Implement comprehensive transaction monitoring",
                    "Use network analysis tools for fund flow tracking",
                    "Enhanced due diligence for high-risk customers",
                    "Regular SAR filing and regulatory compliance",
                    "Cross-border information sharing"
                ],
                regulatory_notes="Layering activities trigger SAR filing requirements under BSA and may require OFAC screening.",
                tags=["money_laundering", "layering", "structuring", "international", "SAR", "network_analysis"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_004",
                title="Synthetic Identity Fraud", 
                pattern_type="IDENTITY_FRAUD",
                severity="HIGH",
                description="Creation of fake identities using combinations of real and fabricated personal information to establish credit and conduct fraud.",
                indicators=[
                    "New accounts with limited credit history but high credit scores",
                    "Mismatched personal information (age, address, SSN)",
                    "Rapid credit building followed by bust-out behavior",
                    "Multiple accounts with similar but not identical information",
                    "Addresses that don't exist or are mailbox services"
                ],
                detection_methods=[
                    "Cross-reference verification across multiple databases",
                    "Velocity analysis for new account openings",
                    "Address and identity validation services",
                    "Social network analysis for linked accounts",
                    "Credit profile inconsistency detection"
                ],
                case_studies=[
                    {
                        "description": "Account opened with SSN belonging to 5-year-old but credit score of 750",
                        "outcome": "Account closed, identity reported to authorities",
                        "indicators_present": ["age_mismatch", "impossible_credit_history"]
                    },
                    {
                        "description": "Ring of 20 synthetic identities using variations of same personal info",
                        "outcome": "Entire network identified and shut down",
                        "indicators_present": ["pattern_similarity", "network_fraud", "velocity"]
                    }
                ],
                prevention_measures=[
                    "Enhanced identity verification processes",
                    "Cross-database validation and consistency checks",
                    "Monitoring for patterns across applications",
                    "Address and phone number verification",
                    "Biometric authentication where possible"
                ],
                regulatory_notes="Synthetic identity fraud may impact credit reporting and requires coordination with credit bureaus.",
                tags=["synthetic_identity", "identity_verification", "credit_fraud", "bust_out", "network_fraud"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_005",
                title="Business Email Compromise (BEC)",
                pattern_type="BUSINESS_FRAUD",
                severity="CRITICAL", 
                description="Sophisticated scam targeting businesses that conduct wire transfers and have suppliers abroad, using social engineering and email fraud.",
                indicators=[
                    "Wire transfer requests with urgent language",
                    "Changes to vendor payment information via email",
                    "Requests from executives to finance teams for transfers",
                    "International wire transfers to new beneficiaries",
                    "Email addresses similar to but not matching legitimate contacts"
                ],
                detection_methods=[
                    "Email authentication and domain verification",
                    "Change request validation procedures",
                    "Pattern analysis for urgent payment requests",
                    "Beneficiary validation for new payees",
                    "Multi-channel verification for large transfers"
                ],
                case_studies=[
                    {
                        "description": "CFO email compromise led to $2M transfer to fraudulent account",
                        "outcome": "Transfer blocked due to verification procedures",
                        "indicators_present": ["executive_impersonation", "large_transfer", "new_beneficiary"]
                    },
                    {
                        "description": "Vendor email compromise changed payment details for monthly invoices",
                        "outcome": "Pattern detected after 3 months, funds partially recovered",
                        "indicators_present": ["vendor_impersonation", "payment_redirect", "ongoing_fraud"]
                    }
                ],
                prevention_measures=[
                    "Implement dual approval for wire transfers",
                    "Use multi-channel verification for payment changes",
                    "Email security training for employees",
                    "Domain authentication and anti-spoofing measures",
                    "Regular vendor information verification"
                ],
                regulatory_notes="BEC incidents may require regulatory reporting and customer notification depending on jurisdiction.",
                tags=["BEC", "email_fraud", "wire_transfer", "social_engineering", "vendor_fraud"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_006",
                title="Romance Scam Money Movement",
                pattern_type="ROMANCE_FRAUD",
                severity="MEDIUM",
                description="Victims of romance scams send money to fraudsters through various payment methods, often involving money mules.",
                indicators=[
                    "Frequent international money transfers to same recipient",
                    "Money transfers to countries known for romance scams",
                    "Victim sends money via multiple payment methods",
                    "Transfers to individuals with no apparent relationship",
                    "Pattern of increasing transfer amounts over time"
                ],
                detection_methods=[
                    "Beneficiary analysis for international transfers",
                    "Geographic risk assessment",
                    "Payment method velocity analysis",
                    "Relationship verification between sender and recipient",
                    "Pattern recognition for escalating amounts"
                ],
                case_studies=[
                    {
                        "description": "Elderly customer sent $50K over 6 months to Nigeria via wire transfers",
                        "outcome": "Customer contacted and educated, transfers blocked",
                        "indicators_present": ["elderly_victim", "international_transfers", "escalating_amounts"]
                    },
                    {
                        "description": "Customer used multiple money service businesses to send $30K to same recipient",
                        "outcome": "Pattern detected, customer intervention prevented further loss",
                        "indicators_present": ["multiple_channels", "same_beneficiary", "velocity"]
                    }
                ],
                prevention_measures=[
                    "Customer education about romance scams",
                    "Monitoring for unusual international transfer patterns",
                    "Beneficiary verification for large transfers",
                    "Warning systems for high-risk transfer patterns",
                    "Collaboration with money service businesses"
                ],
                regulatory_notes="Romance scam reporting may be required under consumer protection regulations.",
                tags=["romance_scam", "international_transfers", "money_mules", "victim_education", "MSB"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_007",
                title="ATM Skimming and Card Cloning",
                pattern_type="CARD_FRAUD",
                severity="HIGH",
                description="Physical devices placed on ATMs to steal card data and PINs for creating cloned cards.",
                indicators=[
                    "Multiple transactions from same compromised ATM location",
                    "Card usage at ATM followed by transactions in different location",
                    "Transactions on cloned cards in different geographic regions",
                    "Pattern of cash withdrawals at maximum daily limits",
                    "Unusual card usage in foreign countries"
                ],
                detection_methods=[
                    "ATM location risk analysis",
                    "Geographic pattern analysis for card usage",
                    "Velocity monitoring for cash withdrawals",
                    "Cross-reference with compromised ATM databases",
                    "International usage pattern analysis"
                ],
                case_studies=[
                    {
                        "description": "ATM in tourist area compromised, 200+ cards cloned and used internationally",
                        "outcome": "ATM operator notified, affected cards reissued",
                        "indicators_present": ["compromised_location", "international_usage", "mass_compromise"]
                    },
                    {
                        "description": "Card used at ATM in US, then cash withdrawals in Eastern Europe same day",
                        "outcome": "Card blocked, customer contacted immediately",
                        "indicators_present": ["impossible_travel", "cash_withdrawal_pattern"]
                    }
                ],
                prevention_measures=[
                    "Regular ATM inspection and monitoring",
                    "Real-time transaction monitoring for geographic anomalies",
                    "Customer alerts for international usage",
                    "EMV chip implementation to prevent cloning",
                    "Collaboration with law enforcement and ATM operators"
                ],
                regulatory_notes="Card skimming incidents require notification to card networks and may require customer notification.",
                tags=["ATM_skimming", "card_cloning", "geographic_fraud", "cash_withdrawal", "international"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_008",
                title="Mobile Payment Fraud",
                pattern_type="DIGITAL_FRAUD",
                severity="MEDIUM",
                description="Fraudulent activities exploiting mobile payment platforms through compromised accounts, stolen devices, or social engineering.",
                indicators=[
                    "Mobile payments from new or unregistered devices",
                    "Multiple failed authentication attempts on mobile app",
                    "Sudden change in payment patterns after device change",
                    "P2P payments to unknown recipients",
                    "Mobile payments from high-risk geographic locations"
                ],
                detection_methods=[
                    "Device registration and fingerprinting",
                    "Behavioral analysis for mobile app usage",
                    "P2P payment recipient verification",
                    "Location and velocity analysis for mobile payments",
                    "Authentication pattern analysis"
                ],
                case_studies=[
                    {
                        "description": "Stolen phone used to make $2K in mobile payments within hours",
                        "outcome": "Device blacklisted, payments reversed, account secured",
                        "indicators_present": ["new_device", "velocity", "pattern_change"]
                    },
                    {
                        "description": "Account compromised through SIM swap, mobile payments redirected",
                        "outcome": "SIM swap detected, account frozen, payments blocked",
                        "indicators_present": ["SIM_swap", "authentication_bypass", "payment_redirect"]
                    }
                ],
                prevention_measures=[
                    "Strong device authentication and registration",
                    "Biometric authentication for mobile payments",
                    "Real-time transaction monitoring for mobile channels",
                    "P2P payment limits and recipient verification",
                    "Integration with telecom providers for SIM swap detection"
                ],
                regulatory_notes="Mobile payment fraud may require reporting under digital payment regulations.",
                tags=["mobile_payment", "device_fraud", "P2P", "SIM_swap", "biometric_auth"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_009",
                title="Cryptocurrency Money Laundering",
                pattern_type="CRYPTO_FRAUD",
                severity="HIGH",
                description="Use of cryptocurrency exchanges and wallets to launder money through digital asset conversions and transfers.",
                indicators=[
                    "Large cash deposits followed by crypto purchases",
                    "Rapid conversion between multiple cryptocurrencies",
                    "Use of privacy coins (Monero, Zcash) for transactions",
                    "Crypto transfers to high-risk or sanctioned addresses",
                    "Pattern of crypto-to-cash conversions through multiple exchanges"
                ],
                detection_methods=[
                    "Blockchain analysis and transaction tracing",
                    "Exchange monitoring and wallet address verification",
                    "Pattern analysis for crypto conversion behaviors",
                    "Cross-reference with known illicit addresses",
                    "Velocity analysis for crypto transactions"
                ],
                case_studies=[
                    {
                        "description": "Criminal organization used multiple exchanges to convert $5M through Bitcoin",
                        "outcome": "Blockchain analysis traced funds, exchanges cooperated in investigation",
                        "indicators_present": ["multi_exchange", "large_amounts", "rapid_conversion"]
                    },
                    {
                        "description": "Ransomware proceeds laundered through privacy coins and DEX platforms",
                        "outcome": "Partial fund recovery through blockchain analysis",
                        "indicators_present": ["privacy_coins", "DEX_usage", "ransomware_source"]
                    }
                ],
                prevention_measures=[
                    "Enhanced due diligence for crypto customers",
                    "Blockchain analysis tools for transaction monitoring",
                    "Collaboration with crypto exchanges and regulators",
                    "Monitoring of known illicit wallet addresses",
                    "Regular training on crypto fraud patterns"
                ],
                regulatory_notes="Crypto money laundering requires SAR filing and may involve OFAC sanctions screening.",
                tags=["cryptocurrency", "blockchain_analysis", "money_laundering", "privacy_coins", "exchanges"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_010",
                title="Invoice Fraud and Payment Redirection",
                pattern_type="BUSINESS_FRAUD",
                severity="MEDIUM",
                description="Fraudsters intercept and modify legitimate invoices or create fake invoices to redirect payments to fraudulent accounts.",
                indicators=[
                    "Changes to vendor banking information via email",
                    "Invoices with new bank account details",
                    "Payments to new beneficiaries without proper verification",
                    "Email communications requesting urgent payment changes",
                    "Invoices from vendors not in approved vendor list"
                ],
                detection_methods=[
                    "Vendor master file change monitoring",
                    "Email verification for payment instruction changes",
                    "New beneficiary verification procedures",
                    "Invoice authenticity verification",
                    "Pattern analysis for urgent payment requests"
                ],
                case_studies=[
                    {
                        "description": "Vendor email compromised, payment instructions changed for $500K invoice",
                        "outcome": "Dual verification process caught fraud before payment",
                        "indicators_present": ["email_compromise", "payment_redirect", "large_amount"]
                    },
                    {
                        "description": "Fake invoices created for services never provided to multiple companies",
                        "outcome": "Cross-industry information sharing identified pattern",
                        "indicators_present": ["fake_invoices", "multi_victim", "service_fraud"]
                    }
                ],
                prevention_measures=[
                    "Dual approval for vendor information changes",
                    "Out-of-band verification for payment instruction changes",
                    "Vendor master file access controls",
                    "Regular vendor information audits",
                    "Invoice verification procedures"
                ],
                regulatory_notes="Invoice fraud may require reporting under business fraud regulations.",
                tags=["invoice_fraud", "payment_redirect", "vendor_fraud", "email_compromise", "verification"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_011",
                title="Identity Theft for Account Opening",
                pattern_type="IDENTITY_FRAUD",
                severity="HIGH",
                description="Using stolen personal information to open new financial accounts for fraudulent purposes.",
                indicators=[
                    "Account applications with inconsistent information",
                    "Multiple applications from same IP/device with different identities",
                    "Applications using recently deceased persons' information",
                    "Rapid account opening followed by maximum credit utilization",
                    "Applications with information from data breaches"
                ],
                detection_methods=[
                    "Cross-reference with death records and data breach databases",
                    "Device fingerprinting across applications",
                    "Velocity monitoring for account applications",
                    "Identity verification through multiple data sources",
                    "Behavioral analysis during application process"
                ],
                case_studies=[
                    {
                        "description": "Fraudster opened 50+ accounts using stolen tax return information",
                        "outcome": "Pattern analysis identified common data source, accounts closed",
                        "indicators_present": ["velocity", "tax_data_theft", "pattern_similarity"]
                    },
                    {
                        "description": "Dead person's identity used to open high-limit credit accounts",
                        "outcome": "Death record check would have prevented fraud",
                        "indicators_present": ["deceased_identity", "high_limit_request"]
                    }
                ],
                prevention_measures=[
                    "Enhanced identity verification processes",
                    "Cross-reference with death records and watchlists",
                    "Device and IP analysis for applications",
                    "Real-time identity verification services",
                    "Monitoring for data breach victim information"
                ],
                regulatory_notes="Identity theft for account opening requires customer notification and regulatory reporting.",
                tags=["identity_theft", "account_opening", "deceased_identity", "data_breach", "verification"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_012",
                title="Gambling and Gaming Fraud",
                pattern_type="GAMING_FRAUD",
                severity="MEDIUM",
                description="Fraudulent activities in online gambling and gaming platforms including bonus abuse, collusion, and payment fraud.",
                indicators=[
                    "Multiple accounts from same household/IP for bonus abuse",
                    "Rapid deposit and withdrawal patterns",
                    "Unusual betting patterns or game play",
                    "Collusion between accounts in multiplayer games",
                    "Chargebacks after gambling losses"
                ],
                detection_methods=[
                    "Multi-accounting detection through device/IP analysis",
                    "Behavioral analysis for gaming patterns",
                    "Network analysis for account relationships",
                    "Payment pattern analysis for deposits/withdrawals",
                    "Bonus abuse pattern recognition"
                ],
                case_studies=[
                    {
                        "description": "Player created 20 accounts to claim new player bonuses",
                        "outcome": "Device fingerprinting identified linked accounts, bonuses forfeited",
                        "indicators_present": ["multi_accounting", "bonus_abuse", "same_device"]
                    },
                    {
                        "description": "Poker players colluded across multiple tables using shared information",
                        "outcome": "Behavioral analysis detected unusual play patterns",
                        "indicators_present": ["collusion", "unusual_patterns", "coordinated_play"]
                    }
                ],
                prevention_measures=[
                    "Strong device and identity verification",
                    "Real-time behavioral monitoring",
                    "Network analysis for account relationships",
                    "Anti-bonus abuse controls",
                    "Regular audit of gaming patterns"
                ],
                regulatory_notes="Gaming fraud may require reporting to gaming regulators and financial authorities.",
                tags=["gambling_fraud", "gaming", "bonus_abuse", "multi_accounting", "collusion"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_013",
                title="Check Fraud and Kiting",
                pattern_type="CHECK_FRAUD",
                severity="MEDIUM",
                description="Fraudulent use of checks including alteration, counterfeiting, and check kiting schemes.",
                indicators=[
                    "Deposits of altered or suspicious checks",
                    "Rapid withdrawal after check deposit before clearing",
                    "Deposits and withdrawals across multiple accounts (kiting)",
                    "Checks with inconsistent fonts, routing numbers, or signatures",
                    "Large check deposits from unknown sources"
                ],
                detection_methods=[
                    "Check image analysis for alterations",
                    "Velocity monitoring for deposits and withdrawals",
                    "Cross-account analysis for kiting patterns",
                    "Positive pay systems for business accounts",
                    "Signature verification and handwriting analysis"
                ],
                case_studies=[
                    {
                        "description": "Check kiting scheme using 5 banks to float $100K for 2 weeks",
                        "outcome": "Cross-bank communication identified pattern, accounts closed",
                        "indicators_present": ["multi_bank", "float_scheme", "velocity"]
                    },
                    {
                        "description": "Counterfeit checks printed with stolen account information",
                        "outcome": "Check verification system identified inconsistencies",
                        "indicators_present": ["counterfeit", "account_theft", "verification_failure"]
                    }
                ],
                prevention_measures=[
                    "Check verification and positive pay systems",
                    "Hold periods for large or unusual check deposits",
                    "Cross-account monitoring for kiting patterns",
                    "Advanced check image analysis",
                    "Customer education about check security"
                ],
                regulatory_notes="Check fraud requires reporting to check verification systems and may involve federal prosecution.",
                tags=["check_fraud", "kiting", "counterfeit", "alteration", "positive_pay"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_014",
                title="Social Engineering for Financial Access",
                pattern_type="SOCIAL_ENGINEERING",
                severity="HIGH",
                description="Psychological manipulation techniques used to gain unauthorized access to financial accounts or sensitive information.",
                indicators=[
                    "Customer service calls requesting unusual account access",
                    "Urgent requests for account information or credentials",
                    "Impersonation of bank employees or government officials",
                    "Requests to bypass normal security procedures",
                    "Multiple contact attempts using different stories"
                ],
                detection_methods=[
                    "Call authentication and verification procedures",
                    "Pattern analysis for unusual customer service requests",
                    "Staff training for social engineering recognition",
                    "Recording and analysis of suspicious calls",
                    "Cross-channel verification requirements"
                ],
                case_studies=[
                    {
                        "description": "Caller impersonated bank fraud department to obtain customer PINs",
                        "outcome": "Customer service training improved, verification procedures strengthened",
                        "indicators_present": ["impersonation", "PIN_request", "fraud_department_claim"]
                    },
                    {
                        "description": "Elderly customers targeted with urgent account security claims",
                        "outcome": "Vulnerable customer protection protocols implemented",
                        "indicators_present": ["elderly_targeting", "urgency", "security_claims"]
                    }
                ],
                prevention_measures=[
                    "Comprehensive staff training on social engineering",
                    "Strict authentication procedures for account access",
                    "Customer education about legitimate bank communications",
                    "Recording and monitoring of customer service interactions",
                    "Special protections for vulnerable customers"
                ],
                regulatory_notes="Social engineering incidents may require customer notification and regulatory reporting.",
                tags=["social_engineering", "customer_service", "impersonation", "authentication", "elderly_fraud"],
                created_at="2024-01-15T00:00:00Z"
            ),
            
            FraudPatternDocument(
                id="fp_015",
                title="Merchant Fraud and Friendly Fraud",
                pattern_type="MERCHANT_FRAUD",
                severity="MEDIUM",
                description="Fraudulent chargebacks and disputes including legitimate purchases disputed as fraud (friendly fraud) and merchant collusion.",
                indicators=[
                    "High chargeback rates for specific merchants",
                    "Customers with patterns of disputing legitimate purchases",
                    "Chargebacks filed immediately after purchase",
                    "Disputes for digital goods after consumption",
                    "Coordinated chargeback attacks on merchants"
                ],
                detection_methods=[
                    "Chargeback rate monitoring by merchant and customer",
                    "Pattern analysis for dispute behaviors",
                    "Cross-reference purchase and dispute timelines",
                    "Merchant risk assessment and monitoring",
                    "Customer dispute history analysis"
                ],
                case_studies=[
                    {
                        "description": "Customer disputed $5K in legitimate purchases claiming fraud",
                        "outcome": "Purchase evidence and delivery confirmation provided to card network",
                        "indicators_present": ["friendly_fraud", "legitimate_purchases", "delivery_proof"]
                    },
                    {
                        "description": "Coordinated attack on e-commerce merchant with 200+ chargebacks",
                        "outcome": "Pattern analysis identified organized attack, chargebacks reversed",
                        "indicators_present": ["coordinated_attack", "velocity", "organized_fraud"]
                    }
                ],
                prevention_measures=[
                    "Detailed transaction records and delivery confirmation",
                    "Customer communication and satisfaction monitoring",
                    "Chargeback response and evidence management",
                    "Merchant education about fraud prevention",
                    "Industry information sharing about fraud patterns"
                ],
                regulatory_notes="Merchant fraud may require reporting to card networks and payment processors.",
                tags=["friendly_fraud", "chargebacks", "merchant_fraud", "disputes", "organized_attacks"],
                created_at="2024-01-15T00:00:00Z"
            )
        ]
        
        return patterns
    
    async def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific fraud pattern by ID"""
        try:
            result = self.collection.get(ids=[pattern_id])
            
            if result["documents"]:
                return {
                    "status": "success",
                    "pattern_id": pattern_id,
                    "content": result["documents"][0],
                    "metadata": result["metadatas"][0]
                }
            else:
                return {
                    "status": "not_found",
                    "pattern_id": pattern_id
                }
                
        except Exception as e:
            logger.error(f"Error retrieving pattern {pattern_id}: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "pattern_id": pattern_id
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the fraud pattern collection"""
        try:
            count = self.collection.count()
            
            # Get sample of patterns for analysis
            sample = self.collection.get(limit=min(count, 20))
            
            pattern_types = {}
            severities = {}
            
            for metadata in sample["metadatas"]:
                pattern_type = metadata.get("pattern_type", "unknown")
                severity = metadata.get("severity", "unknown")
                
                pattern_types[pattern_type] = pattern_types.get(pattern_type, 0) + 1
                severities[severity] = severities.get(severity, 0) + 1
            
            return {
                "total_patterns": count,
                "pattern_types": pattern_types,
                "severities": severities,
                "embedding_model": self.embedding_function.model_name,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "error": str(e),
                "total_patterns": 0
            }


# Create tool wrapper for agent integration
class FraudPatternSearchTool:
    """Tool wrapper for fraud pattern search functionality"""
    
    def __init__(self, api_key: str):
        self.rag_system = FraudPatternRAG(api_key)
    
    async def search_fraud_patterns(self, query: str, n_results: int = 5, 
                                  pattern_type: Optional[str] = None,
                                  severity: Optional[str] = None) -> Dict[str, Any]:
        """
        Search fraud patterns tool for AI agent
        
        Args:
            query: Description of fraud indicators or patterns to search for
            n_results: Number of results to return (default: 5)
            pattern_type: Filter by pattern type (optional)
            severity: Filter by severity level (optional)
            
        Returns:
            Structured search results with relevant fraud patterns
        """
        
        filter_criteria = {}
        if pattern_type:
            filter_criteria["pattern_type"] = pattern_type.upper()
        if severity:
            filter_criteria["severity"] = severity.upper()
        
        result = await self.rag_system.search_fraud_patterns(
            query=query,
            n_results=n_results,
            filter_criteria=filter_criteria if filter_criteria else None
        )
        
        logger.info(f"Fraud pattern search for '{query}' returned {result.get('total_results', 0)} results")
        
        return result


# Export for use by the AI agent
__all__ = ["FraudPatternRAG", "FraudPatternSearchTool"]