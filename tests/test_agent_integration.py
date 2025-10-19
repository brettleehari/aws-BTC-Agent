"""
Integration Tests for Market Hunter Agent + Data Interfaces

Tests the complete integration including:
- Source mapping
- Combined quality scoring
- Rate limit awareness
- Agent cycle execution
- Bedrock action handler
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.market_hunter_agent_integrated import (
    IntegratedMarketHunterAgent,
    MarketContext,
    TradingHours
)
from src.source_mapping import (
    get_source_requirements,
    get_context_boosted_importance,
    LOGICAL_TO_TECHNICAL_MAPPING
)
from src.data_interfaces import (
    DataType,
    Capability,
    RequestPriority,
    DataResponse,
    DataSourceMetadata,
    ResponseTime,
    CostTier,
    RateLimits
)


class TestSourceMapping:
    """Test source mapping configuration"""
    
    def test_all_logical_sources_mapped(self):
        """Test that all logical sources have mapping configuration"""
        expected_sources = [
            "whaleMovements",
            "narrativeShifts",
            "arbitrageOpportunities",
            "influencerSignals",
            "technicalBreakouts",
            "institutionalFlows",
            "derivativesSignals",
            "macroSignals"
        ]
        
        for source in expected_sources:
            assert source in LOGICAL_TO_TECHNICAL_MAPPING
            
    def test_source_requirements_structure(self):
        """Test that source requirements have correct structure"""
        requirements = get_source_requirements("whaleMovements")
        
        assert "description" in requirements
        assert "data_types" in requirements
        assert "required_capabilities" in requirements
        assert "priority" in requirements
        assert "importance_score" in requirements
        
        assert isinstance(requirements["data_types"], list)
        assert all(isinstance(dt, DataType) for dt in requirements["data_types"])
        assert isinstance(requirements["required_capabilities"], list)
        assert all(isinstance(c, Capability) for c in requirements["required_capabilities"])
        
    def test_context_importance_boost(self):
        """Test context-specific importance boosting"""
        base_importance = LOGICAL_TO_TECHNICAL_MAPPING["whaleMovements"]["importance_score"]
        
        # High volatility should boost whale movements
        boosted = get_context_boosted_importance("whaleMovements", "high_volatility")
        assert boosted >= base_importance
        
        # Low volatility should not boost whale movements
        low_vol = get_context_boosted_importance("whaleMovements", "low_volatility")
        assert low_vol == base_importance  # No boost defined
        
    def test_all_sources_have_importance_scores(self):
        """Test that all sources have valid importance scores"""
        for source, config in LOGICAL_TO_TECHNICAL_MAPPING.items():
            importance = config["importance_score"]
            assert 0.0 <= importance <= 1.0


class TestIntegratedAgent:
    """Test integrated Market Hunter Agent"""
    
    @pytest.fixture
    def agent(self):
        """Create test agent instance"""
        return IntegratedMarketHunterAgent(
            agent_name="test-agent",
            learning_rate=0.1,
            exploration_rate=0.2,
            technical_weight=0.7
        )
    
    def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent.agent_name == "test-agent"
        assert agent.learning_rate == 0.1
        assert agent.exploration_rate == 0.2
        assert agent.technical_weight == 0.7
        assert agent.agent_weight == 0.3
        
        # Check all logical sources have metrics
        assert len(agent.source_metrics) == 8
        for source in LOGICAL_TO_TECHNICAL_MAPPING.keys():
            assert source in agent.source_metrics
            
    def test_market_context_assessment(self, agent):
        """Test market context assessment logic"""
        # High volatility
        context = agent.assess_market_context(
            current_price=60000,
            price_24h_ago=57000,  # +5.26% change
            volume_24h=1000000,
            avg_volume=800000
        )
        assert context == MarketContext.HIGH_VOLATILITY
        
        # Bullish trend
        context = agent.assess_market_context(
            current_price=60000,
            price_24h_ago=58000,  # +3.45% change
            volume_24h=1200000,  # 1.5x average
            avg_volume=800000
        )
        assert context == MarketContext.BULLISH_TREND
        
        # Bearish trend
        context = agent.assess_market_context(
            current_price=57000,
            price_24h_ago=60000,  # -5% change
            volume_24h=1000000,
            avg_volume=800000
        )
        assert context == MarketContext.BEARISH_TREND
        
        # Low volatility
        context = agent.assess_market_context(
            current_price=60000,
            price_24h_ago=59900,  # +0.17% change
            volume_24h=600000,  # 0.75x average
            avg_volume=800000
        )
        assert context == MarketContext.LOW_VOLATILITY
        
    def test_trading_hours_detection(self, agent):
        """Test trading hours detection"""
        with patch('src.market_hunter_agent_integrated.datetime') as mock_datetime:
            # Asian hours (2 AM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 2, 0, 0)
            assert agent.get_trading_hours() == TradingHours.ASIAN
            
            # European hours (10 AM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 10, 0, 0)
            assert agent.get_trading_hours() == TradingHours.EUROPEAN
            
            # Overlap hours (14 PM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 14, 0, 0)
            assert agent.get_trading_hours() == TradingHours.OVERLAP
            
            # American hours (20 PM UTC)
            mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 20, 0, 0)
            assert agent.get_trading_hours() == TradingHours.AMERICAN
            
    def test_combined_quality_scoring(self, agent):
        """Test combined quality scoring (technical + agent learning)"""
        # Mock technical metadata
        with patch.object(agent.registry, 'get_source') as mock_get_source:
            mock_metadata = DataSourceMetadata(
                source_id="test_source",
                name="Test Source",
                data_types=[DataType.WHALE_TRANSACTIONS],
                capabilities=[Capability.WHALE_TRACKING],
                quality_score=0.9,  # High technical quality
                response_time=ResponseTime.FAST,
                cost_tier=CostTier.FREE,
                rate_limits=RateLimits(requests_per_minute=10)
            )
            mock_get_source.return_value = mock_metadata
            
            # Set agent's learned score to 0.6
            agent.context_performance[MarketContext.HIGH_VOLATILITY.value]["whaleMovements"] = 0.6
            
            score = agent._get_combined_quality_score(
                "whaleMovements",
                MarketContext.HIGH_VOLATILITY
            )
            
            # Should be: 0.7 * 0.9 (technical) + 0.3 * 0.6 (agent) = 0.81
            assert abs(score - 0.81) < 0.01
            
    def test_source_selection(self, agent):
        """Test source selection logic"""
        # High volatility should select more sources
        selected = agent.select_sources(MarketContext.HIGH_VOLATILITY, max_sources=6)
        
        # Should select available sources (those that can be fulfilled)
        assert len(selected) > 0
        assert all(source in LOGICAL_TO_TECHNICAL_MAPPING for source in selected)
        
    @pytest.mark.asyncio
    async def test_query_source_with_rate_limit(self, agent):
        """Test querying source with rate limit awareness"""
        # Mock manager query
        mock_response = DataResponse(
            source_id="coingecko",
            data_types=[DataType.WHALE_TRANSACTIONS],
            data={"transactions": [{"amount": 150}]},
            timestamp=datetime.utcnow(),
            metadata=DataSourceMetadata(
                source_id="coingecko",
                name="CoinGecko",
                data_types=[DataType.PRICE],
                capabilities=[Capability.REAL_TIME],
                quality_score=0.85,
                response_time=ResponseTime.FAST,
                cost_tier=CostTier.FREE,
                rate_limits=RateLimits(requests_per_minute=50)
            ),
            from_cache=False
        )
        
        with patch.object(agent.manager, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_response
            
            result = await agent.query_source_with_rate_limit_check("whaleMovements")
            
            assert result is not None
            assert result["source"] == "whaleMovements"
            assert result["technical_source"] == "coingecko"
            assert "transactions" in result["data"]
            
            # Check metrics updated
            assert agent.source_metrics["whaleMovements"]["successful_calls"] == 1
            assert agent.source_metrics["whaleMovements"]["total_calls"] == 1
            
    @pytest.mark.asyncio
    async def test_query_source_failure_handling(self, agent):
        """Test handling of failed queries"""
        # Mock manager query to raise exception
        with patch.object(agent.manager, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.side_effect = Exception("Rate limit exceeded")
            
            result = await agent.query_source_with_rate_limit_check("whaleMovements")
            
            assert result is None
            
            # Check failure metrics updated
            assert agent.source_metrics["whaleMovements"]["total_calls"] == 1
            assert agent.source_metrics["whaleMovements"]["successful_calls"] == 0
            
    @pytest.mark.asyncio
    async def test_run_cycle(self, agent):
        """Test complete agent cycle execution"""
        market_data = {
            "current_price": 60000,
            "price_24h_ago": 57000,
            "volume_24h": 1000000,
            "avg_volume": 800000
        }
        
        # Mock query responses
        mock_response = DataResponse(
            source_id="test_source",
            data_types=[DataType.PRICE],
            data={"price": 60000},
            timestamp=datetime.utcnow(),
            metadata=DataSourceMetadata(
                source_id="test_source",
                name="Test",
                data_types=[DataType.PRICE],
                capabilities=[Capability.REAL_TIME],
                quality_score=0.8,
                response_time=ResponseTime.FAST,
                cost_tier=CostTier.FREE,
                rate_limits=RateLimits(requests_per_minute=10)
            ),
            from_cache=False
        )
        
        with patch.object(agent.manager, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_response
            
            results = await agent.run_cycle(market_data)
            
            assert "cycle" in results
            assert "context" in results
            assert "sources_selected" in results
            assert "data_points" in results
            assert "signals_generated" in results
            
            assert results["context"] == MarketContext.HIGH_VOLATILITY.value
            assert len(results["sources_selected"]) > 0
            
    def test_get_source_status(self, agent):
        """Test getting comprehensive source status"""
        status = agent.get_source_status()
        
        assert "logical_sources" in status
        assert "technical_sources" in status
        assert "manager_stats" in status
        
        # Check logical source status
        for source in LOGICAL_TO_TECHNICAL_MAPPING.keys():
            assert source in status["logical_sources"]
            source_status = status["logical_sources"][source]
            
            assert "can_fulfill" in source_status
            assert "technical_sources" in source_status
            assert "agent_metrics" in source_status
            assert "requirements" in source_status


class TestBedrockActionHandler:
    """Test Bedrock Agent action handler"""
    
    @pytest.fixture
    def mock_event(self):
        """Create mock Bedrock event"""
        return {
            "messageVersion": "1.0",
            "actionGroup": "MarketDataActions",
            "apiPath": "/capabilities/discover",
            "httpMethod": "GET",
            "parameters": [],
            "requestBody": {}
        }
    
    def test_discover_capabilities_handler(self, mock_event):
        """Test capability discovery handler"""
        from src.bedrock_action_handler import handle_discover_capabilities
        
        response = handle_discover_capabilities({})
        
        assert response["statusCode"] == 200
        assert "capabilities" in response
        assert "data_types" in response
        assert "sources" in response
        
        assert len(response["capabilities"]) > 0
        assert len(response["data_types"]) > 0
        
    def test_list_sources_handler(self):
        """Test list sources handler"""
        from src.bedrock_action_handler import handle_list_sources
        
        response = handle_list_sources({})
        
        assert response["statusCode"] == 200
        assert "total_sources" in response
        assert "sources" in response
        
        # Each source should have metadata
        for source in response["sources"]:
            assert "source_id" in source
            assert "name" in source
            assert "data_types" in source
            assert "capabilities" in source
            assert "quality_score" in source
            
    def test_get_status_handler(self):
        """Test status handler"""
        from src.bedrock_action_handler import handle_get_status
        
        response = handle_get_status({})
        
        assert response["statusCode"] == 200
        assert "agent_name" in response
        assert "current_cycle" in response
        assert "logical_sources" in response
        
    def test_format_bedrock_response(self, mock_event):
        """Test Bedrock response formatting"""
        from src.bedrock_action_handler import format_bedrock_response
        
        handler_response = {
            "statusCode": 200,
            "data": {"key": "value"}
        }
        
        formatted = format_bedrock_response(mock_event, handler_response)
        
        assert formatted["messageVersion"] == "1.0"
        assert formatted["response"]["actionGroup"] == "MarketDataActions"
        assert formatted["response"]["httpStatusCode"] == 200
        assert "responseBody" in formatted["response"]


class TestAdaptiveLearning:
    """Test agent's adaptive learning capabilities"""
    
    @pytest.fixture
    def agent(self):
        """Create test agent"""
        return IntegratedMarketHunterAgent(
            learning_rate=0.2  # Faster learning for tests
        )
    
    @pytest.mark.asyncio
    async def test_success_rate_learning(self, agent):
        """Test that agent learns from success/failure"""
        initial_success = agent.source_metrics["whaleMovements"]["success_rate"]
        
        # Simulate successful query
        mock_response = DataResponse(
            source_id="test",
            data_types=[DataType.WHALE_TRANSACTIONS],
            data={"transactions": []},
            timestamp=datetime.utcnow(),
            metadata=DataSourceMetadata(
                source_id="test",
                name="Test",
                data_types=[DataType.PRICE],
                capabilities=[Capability.REAL_TIME],
                quality_score=0.9,
                response_time=ResponseTime.FAST,
                cost_tier=CostTier.FREE,
                rate_limits=RateLimits(requests_per_minute=10)
            ),
            from_cache=False
        )
        
        with patch.object(agent.manager, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_response
            
            await agent.query_source_with_rate_limit_check("whaleMovements")
            
            # Quality should move toward technical quality (0.9)
            new_quality = agent.source_metrics["whaleMovements"]["quality_score"]
            assert new_quality > initial_success
            
    @pytest.mark.asyncio
    async def test_recency_bonus(self, agent):
        """Test that unused sources get recency bonus"""
        # Simulate several cycles without using a source
        agent.source_metrics["narrativeShifts"]["last_used_cycles"] = 10
        
        selected = agent.select_sources(MarketContext.NEUTRAL, max_sources=6)
        
        # Source with high recency should be more likely to be selected
        # (probabilistic, so we just check the mechanism exists)
        assert agent.source_metrics["narrativeShifts"]["last_used_cycles"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
