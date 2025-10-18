"""
Integration tests for Market Hunter Agent with Amazon Bedrock

Tests real Bedrock Agent invocation, action groups, and end-to-end flows.
These tests require AWS credentials and a deployed Bedrock Agent.
"""

import unittest
import boto3
import json
import time
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_hunter_agent import MarketHunterAgent, DataSource
from market_hunter_with_router import MarketHunterAgentWithRouter


class TestBedrockAgentIntegration(unittest.TestCase):
    """
    Integration tests with real Bedrock Agent
    
    Set these environment variables to run:
    - BEDROCK_AGENT_ID
    - BEDROCK_AGENT_ALIAS_ID
    - AWS_REGION (defaults to us-east-1)
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration"""
        cls.agent_id = os.getenv('BEDROCK_AGENT_ID')
        cls.alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        cls.region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not cls.agent_id or not cls.alias_id:
            raise unittest.SkipTest(
                "Skipping integration tests - set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID"
            )
    
    def setUp(self):
        """Create test agent"""
        self.agent = MarketHunterAgent(
            bedrock_agent_id=self.agent_id,
            bedrock_agent_alias_id=self.alias_id,
            region_name=self.region
        )
    
    def test_bedrock_agent_invoke(self):
        """Test real Bedrock Agent invocation"""
        try:
            # Test simple query
            result = self.agent.query_data_source(
                source=DataSource.WHALE_MOVEMENTS,
                market_context={"btc_price": 45000, "timestamp": datetime.utcnow().isoformat()}
            )
            
            # Should get some response
            self.assertIsNotNone(result)
            
        except Exception as e:
            self.fail(f"Bedrock Agent invocation failed: {str(e)}")
    
    def test_action_group_invocation(self):
        """Test that action groups are properly invoked"""
        # Create Bedrock Agent Runtime client
        client = boto3.client('bedrock-agent-runtime', region_name=self.region)
        
        try:
            # Invoke agent with specific action group request
            response = client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.alias_id,
                sessionId=f'test-session-{int(time.time())}',
                inputText="Query whale movements for large BTC transactions"
            )
            
            # Parse response
            completion = ""
            for event in response.get('completion', []):
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        completion += chunk['bytes'].decode('utf-8')
            
            # Should have received some response
            self.assertGreater(len(completion), 0)
            
        except Exception as e:
            self.fail(f"Action group invocation failed: {str(e)}")
    
    def test_full_cycle_execution(self):
        """Test complete agent execution cycle"""
        market_data = {
            "btc_price": 45000,
            "volatility_24h": 4.2,
            "volume_24h": 28000000000,
            "trend": "bullish"
        }
        
        try:
            result = self.agent.execute_cycle(market_data)
            
            # Verify result structure
            self.assertIn('selected_sources', result)
            self.assertIn('signals', result)
            self.assertIn('execution_time', result)
            
            # Should have selected some sources
            self.assertGreater(len(result['selected_sources']), 0)
            
        except Exception as e:
            self.fail(f"Full cycle execution failed: {str(e)}")
    
    def test_multiple_source_queries(self):
        """Test querying multiple data sources"""
        sources = [
            DataSource.WHALE_MOVEMENTS,
            DataSource.SOCIAL_SENTIMENT,
            DataSource.DERIVATIVES
        ]
        
        results = {}
        for source in sources:
            try:
                result = self.agent.query_data_source(
                    source=source,
                    market_context={"btc_price": 45000}
                )
                results[source] = result
            except Exception as e:
                self.fail(f"Failed to query {source}: {str(e)}")
        
        # Should have results for all sources
        self.assertEqual(len(results), len(sources))


class TestBedrockAgentWithRouter(unittest.TestCase):
    """
    Integration tests for agent with LLM Router
    
    Tests dynamic model selection in real Bedrock environment.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration"""
        cls.agent_id = os.getenv('BEDROCK_AGENT_ID')
        cls.alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')
        cls.region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not cls.agent_id or not cls.alias_id:
            raise unittest.SkipTest(
                "Skipping integration tests - set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID"
            )
    
    def setUp(self):
        """Create test agent with router"""
        self.agent = MarketHunterAgentWithRouter(
            bedrock_agent_id=self.agent_id,
            bedrock_agent_alias_id=self.alias_id,
            region_name=self.region,
            enable_llm_routing=True
        )
    
    def test_router_selects_different_models(self):
        """Test that router selects appropriate models for different tasks"""
        # Simple extraction task
        result1 = self.agent.query_data_source(
            source=DataSource.WHALE_MOVEMENTS,
            market_context={"btc_price": 45000}
        )
        
        # Complex pattern recognition task
        result2 = self.agent.query_data_source(
            source=DataSource.SOCIAL_SENTIMENT,
            market_context={"btc_price": 45000}
        )
        
        # Get usage report
        report = self.agent.get_llm_usage_report()
        
        # Should have used models
        self.assertGreater(report['total_invocations'], 0)
        
        # Should have tracked costs
        self.assertGreater(report['total_cost'], 0)
    
    def test_cost_tracking_accuracy(self):
        """Test that cost tracking is accurate"""
        # Reset usage tracking
        self.agent.llm_router.reset_usage_tracking()
        
        # Execute cycle
        market_data = {
            "btc_price": 45000,
            "volatility_24h": 3.5,
            "trend": "bullish"
        }
        
        result = self.agent.execute_cycle(market_data)
        
        # Get cost report
        report = self.agent.get_llm_usage_report()
        
        # Should have tracked usage
        self.assertGreater(report['total_invocations'], 0)
        self.assertGreater(report['total_cost'], 0)
        
        # Should have model breakdown
        self.assertGreater(len(report['usage_by_model']), 0)


class TestDatabaseIntegration(unittest.TestCase):
    """
    Integration tests for database operations
    
    Tests require PostgreSQL database configured in environment variables.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration"""
        cls.db_host = os.getenv('DB_HOST')
        cls.db_name = os.getenv('DB_NAME')
        cls.db_user = os.getenv('DB_USER')
        cls.db_password = os.getenv('DB_PASSWORD')
        
        if not all([cls.db_host, cls.db_name, cls.db_user, cls.db_password]):
            raise unittest.SkipTest(
                "Skipping database tests - set DB_HOST, DB_NAME, DB_USER, DB_PASSWORD"
            )
    
    def setUp(self):
        """Set up database connection"""
        from database import DatabaseHandler
        
        self.db = DatabaseHandler(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    def test_store_execution_record(self):
        """Test storing agent execution record"""
        execution_data = {
            'agent_id': 'test-agent',
            'selected_sources': ['whale_movements', 'derivatives'],
            'market_context': {'btc_price': 45000},
            'signals_generated': 2,
            'execution_time_seconds': 5.5,
            'status': 'success'
        }
        
        try:
            execution_id = self.db.store_execution(execution_data)
            self.assertIsNotNone(execution_id)
        except Exception as e:
            self.fail(f"Failed to store execution record: {str(e)}")
    
    def test_store_and_retrieve_metrics(self):
        """Test storing and retrieving source metrics"""
        metrics_data = {
            'source': 'whale_movements',
            'success_rate': 0.85,
            'avg_response_time': 1.2,
            'signals_per_query': 0.3,
            'context': {'volatility': 'high'}
        }
        
        try:
            self.db.store_source_metrics(metrics_data)
            
            # Retrieve recent metrics
            retrieved = self.db.get_source_metrics('whale_movements', limit=1)
            self.assertEqual(len(retrieved), 1)
            
        except Exception as e:
            self.fail(f"Failed to store/retrieve metrics: {str(e)}")
    
    def test_store_signals(self):
        """Test storing generated signals"""
        signals = [
            {
                'signal_type': 'WHALE_ACTIVITY',
                'severity': 'high',
                'description': 'Large BTC movement detected',
                'data': {'amount': 250}
            }
        ]
        
        try:
            self.db.store_signals(signals, execution_id=1)
        except Exception as e:
            self.fail(f"Failed to store signals: {str(e)}")


class TestEndToEndFlow(unittest.TestCase):
    """
    End-to-end integration test
    
    Tests complete flow from agent invocation to signal generation and storage.
    Requires all components (Bedrock, Database) to be configured.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test configuration"""
        # Check all required environment variables
        required_vars = [
            'BEDROCK_AGENT_ID',
            'BEDROCK_AGENT_ALIAS_ID',
            'DB_HOST',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise unittest.SkipTest(
                f"Skipping E2E tests - missing: {', '.join(missing)}"
            )
    
    def test_complete_agent_workflow(self):
        """Test complete workflow: assess → select → query → analyze → store"""
        from database import DatabaseHandler
        
        # Initialize agent
        agent = MarketHunterAgentWithRouter(
            bedrock_agent_id=os.getenv('BEDROCK_AGENT_ID'),
            bedrock_agent_alias_id=os.getenv('BEDROCK_AGENT_ALIAS_ID'),
            enable_llm_routing=True
        )
        
        # Initialize database
        db = DatabaseHandler(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        
        # Execute complete cycle
        market_data = {
            "btc_price": 45000,
            "volatility_24h": 4.2,
            "volume_24h": 28000000000,
            "trend": "bullish"
        }
        
        try:
            # Run cycle
            result = agent.execute_cycle(market_data)
            
            # Store execution record
            execution_data = {
                'agent_id': 'market-hunter-integration-test',
                'selected_sources': [str(s) for s in result['selected_sources']],
                'market_context': market_data,
                'signals_generated': len(result['signals']),
                'execution_time_seconds': result['execution_time'],
                'status': 'success'
            }
            execution_id = db.store_execution(execution_data)
            
            # Store signals
            if result['signals']:
                db.store_signals(result['signals'], execution_id)
            
            # Store metrics
            for source, metrics in agent.source_metrics.items():
                metrics_data = {
                    'source': str(source),
                    'success_rate': metrics.success_rate,
                    'avg_response_time': metrics.avg_response_time,
                    'signals_per_query': metrics.signals_per_query,
                    'context': {'volatility': result['context'].volatility}
                }
                db.store_source_metrics(metrics_data)
            
            # Verify everything succeeded
            self.assertIsNotNone(execution_id)
            self.assertGreater(len(result['selected_sources']), 0)
            
            # Check LLM usage
            llm_report = agent.get_llm_usage_report()
            self.assertGreater(llm_report['total_invocations'], 0)
            
            print(f"\n✅ End-to-end test successful!")
            print(f"   Execution ID: {execution_id}")
            print(f"   Sources queried: {len(result['selected_sources'])}")
            print(f"   Signals generated: {len(result['signals'])}")
            print(f"   LLM cost: ${llm_report['total_cost']:.4f}")
            
        except Exception as e:
            self.fail(f"End-to-end workflow failed: {str(e)}")


if __name__ == '__main__':
    # Run with: python -m pytest tests/test_integration.py -v
    unittest.main()
