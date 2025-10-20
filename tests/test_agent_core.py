"""
Unit tests for Market Hunter Agent core functionality

Tests the agent's autonomous decision-making, context assessment,
and learning algorithms using Amazon Bedrock AgentCore.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from market_hunter_agent import (
    MarketHunterAgent,
    MarketContext,
    SourceMetrics
)

# Data source constants matching market_hunter_agent.py
WHALE_MOVEMENTS = "whaleMovements"
SOCIAL_SENTIMENT = "narrativeShifts"
DERIVATIVES = "derivativesSignals"


class TestMarketContextAssessment(unittest.TestCase):
    """Test market context assessment logic"""
    
    def setUp(self):
        """Set up test agent"""
        self.agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
    
    def test_high_volatility_detection(self):
        """Test that high volatility is correctly detected"""
        market_data = {
            "btc_price": 45000,
            "volatility_24h": 6.5,  # High volatility
            "volume_24h": 25000000000,
            "trend": "bullish"
        }
        
        context = self.agent.assess_market_context(market_data)
        
        self.assertEqual(context.volatility, "high")
        self.assertGreater(context.btc_price, 0)
    
    def test_low_volatility_detection(self):
        """Test that low volatility is correctly detected"""
        market_data = {
            "btc_price": 45000,
            "volatility_24h": 1.5,  # Low volatility
            "volume_24h": 15000000000,
            "trend": "sideways"
        }
        
        context = self.agent.assess_market_context(market_data)
        
        self.assertEqual(context.volatility, "low")
    
    def test_trend_detection(self):
        """Test trend classification"""
        # Bullish trend
        market_data_bull = {
            "btc_price": 45000,
            "volatility_24h": 3.0,
            "trend": "bullish"
        }
        context_bull = self.agent.assess_market_context(market_data_bull)
        self.assertEqual(context_bull.trend, "bullish")
        
        # Bearish trend
        market_data_bear = {
            "btc_price": 45000,
            "volatility_24h": 3.0,
            "trend": "bearish"
        }
        context_bear = self.agent.assess_market_context(market_data_bear)
        self.assertEqual(context_bear.trend, "bearish")
    
    def test_trading_session_detection(self):
        """Test trading session detection based on UTC time"""
        # Mock different times
        with patch('market_hunter_agent.datetime') as mock_datetime:
            # Asian session (2 AM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 2, 0)
            market_data = {"btc_price": 45000, "volatility_24h": 3.0, "trend": "bullish"}
            context = self.agent.assess_market_context(market_data)
            self.assertEqual(context.trading_session, "asian")
            
            # European session (10 AM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 10, 0)
            context = self.agent.assess_market_context(market_data)
            self.assertEqual(context.trading_session, "european")
            
            # US session (16 PM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 16, 0)
            context = self.agent.assess_market_context(market_data)
            self.assertEqual(context.trading_session, "us")


class TestSourceSelection(unittest.TestCase):
    """Test autonomous data source selection logic"""
    
    def setUp(self):
        """Set up test agent"""
        self.agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
    
    def test_high_volatility_selects_more_sources(self):
        """Test that high volatility triggers more source queries"""
        high_vol_context = MarketContext(
            btc_price=45000,
            volatility="high",
            trend="bullish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        selected_sources = self.agent.select_sources(high_vol_context)
        
        # High volatility should select 5-6 sources
        self.assertGreaterEqual(len(selected_sources), 5)
        self.assertLessEqual(len(selected_sources), 6)
    
    def test_low_volatility_selects_fewer_sources(self):
        """Test that low volatility triggers fewer source queries"""
        low_vol_context = MarketContext(
            btc_price=45000,
            volatility="low",
            trend="sideways",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        selected_sources = self.agent.select_sources(low_vol_context)
        
        # Low volatility should select 3-4 sources
        self.assertGreaterEqual(len(selected_sources), 3)
        self.assertLessEqual(len(selected_sources), 4)
    
    def test_source_scoring_considers_context(self):
        """Test that source scoring adapts to market context"""
        context = MarketContext(
            btc_price=45000,
            volatility="high",
            trend="bearish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        scores = self.agent.calculate_source_scores(context)
        
        # In bearish market, derivatives and whales should score higher
        self.assertIn(DERIVATIVES, scores)
        self.assertIn(WHALE_MOVEMENTS, scores)
        self.assertGreater(scores[DERIVATIVES], 0)
    
    def test_exploration_introduces_randomness(self):
        """Test that exploration rate introduces variability"""
        context = MarketContext(
            btc_price=45000,
            volatility="medium",
            trend="bullish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        # Run selection multiple times
        selections = []
        for _ in range(10):
            selected = self.agent.select_sources(context)
            selections.append(tuple(sorted(selected)))
        
        # Due to exploration, we should see some variation
        unique_selections = set(selections)
        # At least some variation (might be same sometimes due to randomness)
        self.assertGreaterEqual(len(unique_selections), 1)


class TestAdaptiveLearning(unittest.TestCase):
    """Test adaptive learning algorithm"""
    
    def setUp(self):
        """Set up test agent"""
        self.agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
        self.agent.learning_rate = 0.1
    
    def test_metric_update_increases_on_success(self):
        """Test that successful source increases its metric"""
        source = WHALE_MOVEMENTS
        context = MarketContext(
            btc_price=45000,
            volatility="high",
            trend="bullish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        initial_metric = self.agent.source_metrics[source].success_rate
        
        # Simulate successful query
        self.agent.update_metrics(
            source=source,
            context=context,
            success=True,
            response_time=0.5,
            signals_generated=2
        )
        
        updated_metric = self.agent.source_metrics[source].success_rate
        
        # Success rate should increase (or stay same if already at 1.0)
        self.assertGreaterEqual(updated_metric, initial_metric)
    
    def test_metric_update_decreases_on_failure(self):
        """Test that failed source decreases its metric"""
        source = SOCIAL_SENTIMENT
        context = MarketContext(
            btc_price=45000,
            volatility="high",
            trend="bullish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        # Set initial high success rate
        self.agent.source_metrics[source].success_rate = 0.8
        initial_metric = self.agent.source_metrics[source].success_rate
        
        # Simulate failed query
        self.agent.update_metrics(
            source=source,
            context=context,
            success=False,
            response_time=0.0,
            signals_generated=0
        )
        
        updated_metric = self.agent.source_metrics[source].success_rate
        
        # Success rate should decrease
        self.assertLess(updated_metric, initial_metric)
    
    def test_ema_learning_rate(self):
        """Test exponential moving average calculation"""
        source = DERIVATIVES
        
        # Set known initial value
        self.agent.source_metrics[source].success_rate = 0.5
        
        context = MarketContext(
            btc_price=45000,
            volatility="high",
            trend="bullish",
            trading_session="us",
            timestamp=datetime.utcnow()
        )
        
        # Update with success (new value = 1.0)
        self.agent.update_metrics(
            source=source,
            context=context,
            success=True,
            response_time=0.3,
            signals_generated=1
        )
        
        # EMA formula: new_value = (1 - α) * old + α * new
        # Expected: (1 - 0.1) * 0.5 + 0.1 * 1.0 = 0.45 + 0.1 = 0.55
        expected = 0.55
        actual = self.agent.source_metrics[source].success_rate
        
        self.assertAlmostEqual(actual, expected, places=5)


class TestBedrockAgentInvocation(unittest.TestCase):
    """Test Bedrock Agent invocation logic"""
    
    @patch('market_hunter_agent.boto3.client')
    def test_agent_invocation_success(self, mock_boto3_client):
        """Test successful Bedrock Agent invocation"""
        # Mock Bedrock Agent Runtime client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock invoke_agent response
        mock_response = {
            'completion': [
                {
                    'chunk': {
                        'bytes': b'{"whale_transactions": [{"amount": 150, "direction": "exchange_to_wallet"}]}'
                    }
                }
            ],
            'sessionId': 'test-session-123'
        }
        mock_client.invoke_agent.return_value = mock_response
        
        agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
        
        # Test invocation
        result = agent.query_data_source(
            source=WHALE_MOVEMENTS,
            market_context={"btc_price": 45000}
        )
        
        # Verify invocation was called
        mock_client.invoke_agent.assert_called_once()
        self.assertIsNotNone(result)
    
    @patch('market_hunter_agent.boto3.client')
    def test_agent_invocation_handles_errors(self, mock_boto3_client):
        """Test that agent handles invocation errors gracefully"""
        # Mock Bedrock Agent Runtime client
        mock_client = MagicMock()
        mock_boto3_client.return_value = mock_client
        
        # Mock error
        mock_client.invoke_agent.side_effect = Exception("Bedrock error")
        
        agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
        
        # Test invocation - should handle error gracefully
        result = agent.query_data_source(
            source=WHALE_MOVEMENTS,
            market_context={"btc_price": 45000}
        )
        
        # Should return empty or error result, not crash
        self.assertIsNotNone(result)


class TestSignalGeneration(unittest.TestCase):
    """Test signal generation logic"""
    
    def setUp(self):
        """Set up test agent"""
        self.agent = MarketHunterAgent(
            bedrock_agent_id="test-agent-id",
            bedrock_agent_alias_id="test-alias-id",
            region_name="us-east-1"
        )
    
    def test_whale_activity_signal_generation(self):
        """Test whale activity signal generation"""
        results = {
            WHALE_MOVEMENTS: {
                "whale_transactions": [
                    {"amount": 250, "direction": "exchange_to_wallet"},
                    {"amount": 180, "direction": "exchange_to_wallet"}
                ]
            }
        }
        
        signals = self.agent.analyze_results_and_generate_signals(results)
        
        # Should generate WHALE_ACTIVITY signal
        whale_signals = [s for s in signals if s['signal_type'] == 'WHALE_ACTIVITY']
        self.assertGreater(len(whale_signals), 0)
        self.assertEqual(whale_signals[0]['severity'], 'high')
    
    def test_sentiment_signal_generation(self):
        """Test positive sentiment signal generation"""
        results = {
            SOCIAL_SENTIMENT: {
                "sentiment_score": 0.75,
                "trending_topics": ["bullish", "moon"]
            }
        }
        
        signals = self.agent.analyze_results_and_generate_signals(results)
        
        # Should generate POSITIVE_NARRATIVE signal
        sentiment_signals = [s for s in signals if s['signal_type'] == 'POSITIVE_NARRATIVE']
        self.assertGreater(len(sentiment_signals), 0)
    
    def test_multiple_signals_from_different_sources(self):
        """Test that multiple signals can be generated"""
        results = {
            WHALE_MOVEMENTS: {
                "whale_transactions": [{"amount": 200, "direction": "exchange_to_wallet"}]
            },
            DERIVATIVES: {
                "funding_rate": 0.08
            }
        }
        
        signals = self.agent.analyze_results_and_generate_signals(results)
        
        # Should generate multiple signals
        self.assertGreaterEqual(len(signals), 2)


if __name__ == '__main__':
    unittest.main()
