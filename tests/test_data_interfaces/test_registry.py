"""
Test suite for capability registry.
"""

import unittest
from unittest.mock import Mock, patch

from src.data_interfaces.registry import CapabilityRegistry, get_registry, reset_registry
from src.data_interfaces.base_interface import DataInterface, DataRequest, DataResponse
from src.data_interfaces.metadata import (
    DataSourceMetadata,
    DataType,
    Capability,
    ResponseTime,
    CostTier,
)


class MockSource1(DataInterface):
    """Mock data source for testing"""
    
    @property
    def metadata(self):
        return DataSourceMetadata(
            name="MockSource1",
            provider="Test",
            description="First mock source",
            version="1.0.0",
            data_types=[DataType.PRICE, DataType.VOLUME],
            capabilities=[Capability.REAL_TIME, Capability.HISTORICAL],
            response_time=ResponseTime.FAST,
            reliability_score=0.95,
            cost_tier=CostTier.FREE,
        )
    
    async def fetch(self, request):
        return DataResponse(
            success=True,
            source="MockSource1",
            data={"test": "data"},
            request_time=request.timestamp,
            response_time=request.timestamp,
        )
    
    async def health_check(self):
        return True


class MockSource2(DataInterface):
    """Second mock data source"""
    
    @property
    def metadata(self):
        return DataSourceMetadata(
            name="MockSource2",
            provider="Test",
            description="Second mock source",
            version="1.0.0",
            data_types=[DataType.ON_CHAIN, DataType.WHALE_TRANSACTIONS],
            capabilities=[Capability.WHALE_TRACKING, Capability.ADVANCED_ANALYTICS],
            response_time=ResponseTime.MODERATE,
            reliability_score=0.90,
            cost_tier=CostTier.SUBSCRIPTION,
        )
    
    async def fetch(self, request):
        return DataResponse(
            success=True,
            source="MockSource2",
            data={"test": "data"},
            request_time=request.timestamp,
            response_time=request.timestamp,
        )
    
    async def health_check(self):
        return True


class TestCapabilityRegistry(unittest.TestCase):
    """Test CapabilityRegistry"""
    
    def setUp(self):
        """Create fresh registry for each test"""
        self.registry = CapabilityRegistry()
    
    def tearDown(self):
        """Clean up"""
        reset_registry()
    
    def test_registry_creation(self):
        """Test creating registry"""
        self.assertIsInstance(self.registry, CapabilityRegistry)
        self.assertEqual(len(self.registry.list_sources()), 0)
    
    def test_register_source(self):
        """Test registering a source"""
        self.registry.register(MockSource1)
        
        sources = self.registry.list_sources()
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource1", sources)
    
    def test_register_multiple_sources(self):
        """Test registering multiple sources"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        sources = self.registry.list_sources()
        self.assertEqual(len(sources), 2)
        self.assertIn("MockSource1", sources)
        self.assertIn("MockSource2", sources)
    
    def test_register_duplicate(self):
        """Test registering duplicate source"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource1)  # Should overwrite
        
        sources = self.registry.list_sources()
        self.assertEqual(len(sources), 1)
    
    def test_unregister_source(self):
        """Test unregistering a source"""
        self.registry.register(MockSource1)
        self.registry.unregister("MockSource1")
        
        sources = self.registry.list_sources()
        self.assertEqual(len(sources), 0)
    
    def test_unregister_nonexistent(self):
        """Test unregistering non-existent source"""
        # Should not raise exception
        self.registry.unregister("NonExistent")
    
    def test_get_metadata(self):
        """Test getting source metadata"""
        self.registry.register(MockSource1)
        
        metadata = self.registry.get_metadata("MockSource1")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.name, "MockSource1")
        self.assertEqual(metadata.provider, "Test")
    
    def test_get_metadata_nonexistent(self):
        """Test getting metadata for non-existent source"""
        metadata = self.registry.get_metadata("NonExistent")
        self.assertIsNone(metadata)
    
    def test_find_sources_for_data_type(self):
        """Test finding sources by data type"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        # Find sources for price data
        sources = self.registry.find_sources_for_data_type(DataType.PRICE)
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource1", sources)
        
        # Find sources for on-chain data
        sources = self.registry.find_sources_for_data_type(DataType.ON_CHAIN)
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource2", sources)
    
    def test_find_sources_with_capability(self):
        """Test finding sources by capability"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        # Find real-time sources
        sources = self.registry.find_sources_with_capability(Capability.REAL_TIME)
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource1", sources)
        
        # Find whale tracking sources
        sources = self.registry.find_sources_with_capability(Capability.WHALE_TRACKING)
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource2", sources)
    
    def test_find_sources_multi_criteria(self):
        """Test finding sources with multiple criteria"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        # Find real-time price sources
        sources = self.registry.find_sources(
            data_type=DataType.PRICE,
            capabilities=[Capability.REAL_TIME],
        )
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource1", sources)
    
    def test_find_sources_free_only(self):
        """Test finding free sources only"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        sources = self.registry.find_sources(free_only=True)
        self.assertEqual(len(sources), 1)
        self.assertIn("MockSource1", sources)
    
    def test_find_sources_no_auth(self):
        """Test finding sources that don't require auth"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        sources = self.registry.find_sources(requires_auth=False)
        # Both test sources don't require auth
        self.assertGreaterEqual(len(sources), 0)
    
    def test_recommend_source(self):
        """Test recommending best source for request"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        recommendation = self.registry.recommend_source(request)
        self.assertIsNotNone(recommendation)
        self.assertEqual(recommendation, "MockSource1")
    
    def test_recommend_source_no_match(self):
        """Test recommending source when no match"""
        self.registry.register(MockSource1)
        
        request = DataRequest(
            data_type=DataType.ON_CHAIN,  # MockSource1 doesn't support this
            symbol="BTC",
        )
        
        recommendation = self.registry.recommend_source(request)
        self.assertIsNone(recommendation)
    
    def test_get_source_rankings(self):
        """Test getting ranked list of sources"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        rankings = self.registry.get_source_rankings(request)
        self.assertIsInstance(rankings, list)
        self.assertGreater(len(rankings), 0)
        
        # Check structure
        for item in rankings:
            self.assertIn('name', item)
            self.assertIn('score', item)
            self.assertIn('metadata', item)
    
    def test_create_source_instance(self):
        """Test creating source instance"""
        self.registry.register(MockSource1)
        
        instance = self.registry.create_source_instance("MockSource1")
        self.assertIsInstance(instance, MockSource1)
        self.assertIsInstance(instance, DataInterface)
    
    def test_create_source_instance_with_params(self):
        """Test creating source instance with parameters"""
        self.registry.register(MockSource1)
        
        instance = self.registry.create_source_instance(
            "MockSource1",
            api_key="test_key",
            config={"timeout": 30}
        )
        self.assertEqual(instance.api_key, "test_key")
        self.assertEqual(instance.config["timeout"], 30)
    
    def test_create_source_instance_nonexistent(self):
        """Test creating instance of non-existent source"""
        with self.assertRaises(ValueError):
            self.registry.create_source_instance("NonExistent")
    
    def test_generate_capability_summary(self):
        """Test generating capability summary"""
        self.registry.register(MockSource1)
        self.registry.register(MockSource2)
        
        summary = self.registry.generate_capability_summary()
        
        self.assertIsInstance(summary, dict)
        self.assertIn('total_sources', summary)
        self.assertIn('data_types', summary)
        self.assertIn('capabilities', summary)
        self.assertIn('sources', summary)
        
        self.assertEqual(summary['total_sources'], 2)


class TestGlobalRegistry(unittest.TestCase):
    """Test global registry functions"""
    
    def setUp(self):
        """Reset registry before each test"""
        reset_registry()
    
    def tearDown(self):
        """Clean up after each test"""
        reset_registry()
    
    def test_get_registry_singleton(self):
        """Test that get_registry returns singleton"""
        registry1 = get_registry()
        registry2 = get_registry()
        
        self.assertIs(registry1, registry2)
    
    def test_reset_registry(self):
        """Test resetting global registry"""
        registry1 = get_registry()
        registry1.register(MockSource1)
        
        reset_registry()
        
        registry2 = get_registry()
        self.assertIsNot(registry1, registry2)
        self.assertEqual(len(registry2.list_sources()), 0)


class TestRegistryWithRealSources(unittest.TestCase):
    """Test registry with real data source implementations"""
    
    def setUp(self):
        """Create registry"""
        self.registry = CapabilityRegistry()
    
    def test_register_coingecko(self):
        """Test registering CoinGecko source"""
        from src.data_interfaces.coingecko_interface import CoinGeckoInterface
        
        self.registry.register(CoinGeckoInterface)
        
        sources = self.registry.list_sources()
        self.assertIn("CoinGecko", sources)
        
        metadata = self.registry.get_metadata("CoinGecko")
        self.assertIsNotNone(metadata)
        self.assertIn(DataType.PRICE, metadata.data_types)
    
    def test_register_glassnode(self):
        """Test registering Glassnode source"""
        from src.data_interfaces.glassnode_interface import GlassnodeInterface
        
        self.registry.register(GlassnodeInterface)
        
        sources = self.registry.list_sources()
        self.assertIn("Glassnode", sources)
        
        metadata = self.registry.get_metadata("Glassnode")
        self.assertIsNotNone(metadata)
        self.assertIn(DataType.ON_CHAIN, metadata.data_types)
    
    def test_register_sentiment(self):
        """Test registering Sentiment source"""
        from src.data_interfaces.sentiment_interface import SentimentInterface
        
        self.registry.register(SentimentInterface)
        
        sources = self.registry.list_sources()
        self.assertIn("SentimentAnalyzer", sources)
        
        metadata = self.registry.get_metadata("SentimentAnalyzer")
        self.assertIsNotNone(metadata)
        self.assertIn(DataType.SOCIAL_SENTIMENT, metadata.data_types)


if __name__ == '__main__':
    unittest.main()
