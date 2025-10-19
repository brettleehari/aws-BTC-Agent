"""
Integration tests for data interfaces module.

Tests the complete flow from request to response across multiple sources.
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.data_interfaces import (
    DataType,
    DataRequest,
    DataResponse,
    DataInterfaceManager,
    get_manager,
    reset_manager,
    get_registry,
    reset_registry,
)


class TestManagerBasics(unittest.TestCase):
    """Test basic manager functionality"""
    
    def setUp(self):
        """Set up test manager"""
        reset_manager()
        reset_registry()
        self.manager = DataInterfaceManager()
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
        reset_registry()
    
    def test_manager_creation(self):
        """Test creating manager"""
        self.assertIsInstance(self.manager, DataInterfaceManager)
    
    def test_manager_with_registry(self):
        """Test manager uses registry"""
        self.assertIsNotNone(self.manager.registry)
    
    def test_get_status(self):
        """Test getting manager status"""
        status = self.manager.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('cache_size', status)
        self.assertIn('enable_fallback', status)
        self.assertIn('enable_parallel', status)
        self.assertIn('circuit_breakers', status)
        self.assertIn('registered_sources', status)


class TestManagerCaching(unittest.TestCase):
    """Test manager caching functionality"""
    
    def setUp(self):
        """Set up manager with caching"""
        reset_manager()
        reset_registry()
        self.manager = DataInterfaceManager(cache_ttl=60)
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
        reset_registry()
    
    def test_cache_initially_empty(self):
        """Test cache is empty initially"""
        status = self.manager.get_status()
        self.assertEqual(status['cache_size'], 0)
    
    def test_clear_cache(self):
        """Test clearing cache"""
        self.manager.clear_cache()
        status = self.manager.get_status()
        self.assertEqual(status['cache_size'], 0)


class TestManagerCircuitBreaker(unittest.TestCase):
    """Test circuit breaker functionality"""
    
    def setUp(self):
        """Set up manager"""
        reset_manager()
        reset_registry()
        self.manager = DataInterfaceManager()
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
        reset_registry()
    
    def test_circuit_breaker_closed_initially(self):
        """Test circuit breaker is closed initially"""
        self.assertFalse(self.manager._is_circuit_open("TestSource"))
    
    def test_record_success(self):
        """Test recording successful fetch"""
        self.manager._record_success("TestSource")
        # Should not raise exception
    
    def test_record_failure(self):
        """Test recording failed fetch"""
        self.manager._record_failure("TestSource")
        
        status = self.manager.get_status()
        self.assertIn("TestSource", status['circuit_breakers'])
        self.assertEqual(status['circuit_breakers']['TestSource']['consecutive_failures'], 1)
    
    def test_circuit_opens_after_failures(self):
        """Test circuit opens after multiple failures"""
        for _ in range(5):
            self.manager._record_failure("TestSource")
        
        self.assertTrue(self.manager._is_circuit_open("TestSource"))
    
    def test_reset_circuit_breakers(self):
        """Test resetting all circuit breakers"""
        self.manager._record_failure("TestSource")
        self.manager.reset_circuit_breakers()
        
        status = self.manager.get_status()
        self.assertEqual(len(status['circuit_breakers']), 0)


class TestGlobalManager(unittest.TestCase):
    """Test global manager functions"""
    
    def setUp(self):
        """Reset manager"""
        reset_manager()
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
    
    def test_get_manager_singleton(self):
        """Test get_manager returns singleton"""
        manager1 = get_manager()
        manager2 = get_manager()
        
        self.assertIs(manager1, manager2)
    
    def test_reset_manager(self):
        """Test resetting global manager"""
        manager1 = get_manager()
        reset_manager()
        manager2 = get_manager()
        
        self.assertIsNot(manager1, manager2)


class TestEndToEndIntegration(unittest.TestCase):
    """End-to-end integration tests"""
    
    def setUp(self):
        """Set up clean environment"""
        reset_manager()
        reset_registry()
        
        # Import and register sources
        from src.data_interfaces.coingecko_interface import CoinGeckoInterface
        from src.data_interfaces.sentiment_interface import SentimentInterface
        
        registry = get_registry()
        registry.register(CoinGeckoInterface)
        registry.register(SentimentInterface)
        
        self.manager = get_manager()
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
        reset_registry()
    
    def test_price_request_finds_coingecko(self):
        """Test price request is routed to CoinGecko"""
        sources = self.manager.registry.find_sources_for_data_type(DataType.PRICE)
        self.assertIn("CoinGecko", sources)
    
    def test_sentiment_request_finds_sentiment_analyzer(self):
        """Test sentiment request is routed to SentimentAnalyzer"""
        sources = self.manager.registry.find_sources_for_data_type(DataType.SOCIAL_SENTIMENT)
        self.assertIn("SentimentAnalyzer", sources)
    
    def test_multiple_sources_available(self):
        """Test multiple sources are registered"""
        sources = self.manager.registry.list_sources()
        self.assertGreaterEqual(len(sources), 2)
    
    def test_capability_summary_generation(self):
        """Test generating capability summary"""
        summary = self.manager.registry.generate_capability_summary()
        
        self.assertIn('total_sources', summary)
        self.assertGreater(summary['total_sources'], 0)
        
        self.assertIn('data_types', summary)
        self.assertGreater(len(summary['data_types']), 0)


class TestDataFlowIntegration(unittest.TestCase):
    """Test data flow through the system"""
    
    def setUp(self):
        """Set up test environment"""
        reset_manager()
        reset_registry()
    
    def tearDown(self):
        """Clean up"""
        reset_manager()
        reset_registry()
    
    def test_request_creation(self):
        """Test creating data request"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
            parameters={"vs_currency": "usd"}
        )
        
        self.assertEqual(request.data_type, DataType.PRICE)
        self.assertEqual(request.symbol, "BTC")
        self.assertEqual(request.parameters["vs_currency"], "usd")
    
    def test_response_structure(self):
        """Test response structure"""
        now = datetime.now()
        response = DataResponse(
            success=True,
            source="TestSource",
            data={"price": 50000},
            request_time=now,
            response_time=now,
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.source, "TestSource")
        self.assertIn("price", response.data)


class TestSourceDiscovery(unittest.TestCase):
    """Test source discovery mechanisms"""
    
    def setUp(self):
        """Set up registry with sources"""
        reset_registry()
        
        from src.data_interfaces.coingecko_interface import CoinGeckoInterface
        from src.data_interfaces.glassnode_interface import GlassnodeInterface
        from src.data_interfaces.sentiment_interface import SentimentInterface
        
        registry = get_registry()
        registry.register(CoinGeckoInterface)
        registry.register(GlassnodeInterface)
        registry.register(SentimentInterface)
        
        self.registry = registry
    
    def tearDown(self):
        """Clean up"""
        reset_registry()
    
    def test_discover_price_sources(self):
        """Test discovering sources for price data"""
        sources = self.registry.find_sources_for_data_type(DataType.PRICE)
        self.assertGreater(len(sources), 0)
        self.assertIn("CoinGecko", sources)
    
    def test_discover_on_chain_sources(self):
        """Test discovering sources for on-chain data"""
        sources = self.registry.find_sources_for_data_type(DataType.ON_CHAIN)
        self.assertGreater(len(sources), 0)
        self.assertIn("Glassnode", sources)
    
    def test_discover_sentiment_sources(self):
        """Test discovering sources for sentiment data"""
        sources = self.registry.find_sources_for_data_type(DataType.SOCIAL_SENTIMENT)
        self.assertGreater(len(sources), 0)
        self.assertIn("SentimentAnalyzer", sources)
    
    def test_source_ranking(self):
        """Test source ranking for requests"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC"
        )
        
        rankings = self.registry.get_source_rankings(request)
        self.assertIsInstance(rankings, list)
        
        if rankings:
            # First result should have highest score
            scores = [r['score'] for r in rankings]
            self.assertEqual(scores, sorted(scores, reverse=True))
    
    def test_recommend_best_source(self):
        """Test recommending best source"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC"
        )
        
        recommendation = self.registry.recommend_source(request)
        self.assertIsNotNone(recommendation)
        self.assertIsInstance(recommendation, str)


class TestModuleImports(unittest.TestCase):
    """Test module imports and exports"""
    
    def test_import_data_types(self):
        """Test importing data types"""
        from src.data_interfaces import DataType, Capability
        
        self.assertTrue(hasattr(DataType, 'PRICE'))
        self.assertTrue(hasattr(Capability, 'REAL_TIME'))
    
    def test_import_interfaces(self):
        """Test importing interfaces"""
        from src.data_interfaces import CoinGeckoInterface, SentimentInterface
        
        self.assertIsNotNone(CoinGeckoInterface)
        self.assertIsNotNone(SentimentInterface)
    
    def test_import_manager(self):
        """Test importing manager"""
        from src.data_interfaces import DataInterfaceManager, get_manager
        
        self.assertIsNotNone(DataInterfaceManager)
        manager = get_manager()
        self.assertIsInstance(manager, DataInterfaceManager)
    
    def test_import_openapi_generator(self):
        """Test importing OpenAPI generator"""
        from src.data_interfaces import OpenAPIGenerator, generate_bedrock_action_groups
        
        self.assertIsNotNone(OpenAPIGenerator)
        self.assertIsNotNone(generate_bedrock_action_groups)


if __name__ == '__main__':
    unittest.main()
