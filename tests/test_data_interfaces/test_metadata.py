"""
Test suite for data interfaces metadata models.
"""

import unittest
from datetime import datetime

from src.data_interfaces.metadata import (
    DataType,
    Capability,
    ResponseTime,
    CostTier,
    RateLimits,
    DataSourceMetadata,
)


class TestDataType(unittest.TestCase):
    """Test DataType enum"""
    
    def test_data_type_values(self):
        """Test that all data types have correct values"""
        self.assertEqual(DataType.PRICE.value, "price")
        self.assertEqual(DataType.ON_CHAIN.value, "on_chain")
        self.assertEqual(DataType.WHALE_TRANSACTIONS.value, "whale_transactions")
        self.assertEqual(DataType.SOCIAL_SENTIMENT.value, "social_sentiment")
    
    def test_data_type_membership(self):
        """Test data type membership"""
        self.assertIn(DataType.PRICE, DataType)
        self.assertIn(DataType.EXCHANGE_FLOWS, DataType)


class TestCapability(unittest.TestCase):
    """Test Capability enum"""
    
    def test_capability_values(self):
        """Test that capabilities have correct values"""
        self.assertEqual(Capability.REAL_TIME.value, "real_time")
        self.assertEqual(Capability.WHALE_TRACKING.value, "whale_tracking")
        self.assertEqual(Capability.SENTIMENT_ANALYSIS.value, "sentiment_analysis")
    
    def test_capability_coverage(self):
        """Test that key capabilities are defined"""
        required = [
            Capability.REAL_TIME,
            Capability.HISTORICAL,
            Capability.RATE_LIMITED,
        ]
        for cap in required:
            self.assertIn(cap, Capability)


class TestRateLimits(unittest.TestCase):
    """Test RateLimits dataclass"""
    
    def test_rate_limits_creation(self):
        """Test creating rate limits"""
        limits = RateLimits(
            requests_per_minute=10,
            requests_per_hour=600,
            requests_per_day=10000,
        )
        self.assertEqual(limits.requests_per_minute, 10)
        self.assertEqual(limits.requests_per_hour, 600)
        self.assertEqual(limits.requests_per_day, 10000)
    
    def test_rate_limits_optional(self):
        """Test optional fields"""
        limits = RateLimits(requests_per_minute=10)
        self.assertEqual(limits.requests_per_minute, 10)
        self.assertIsNone(limits.requests_per_hour)
        self.assertIsNone(limits.requests_per_day)


class TestDataSourceMetadata(unittest.TestCase):
    """Test DataSourceMetadata"""
    
    def setUp(self):
        """Create test metadata"""
        self.metadata = DataSourceMetadata(
            name="TestSource",
            provider="TestProvider",
            description="Test data source",
            version="1.0.0",
            data_types=[DataType.PRICE, DataType.VOLUME],
            capabilities=[Capability.REAL_TIME, Capability.HISTORICAL],
            response_time=ResponseTime.FAST,
            reliability_score=0.95,
            cost_tier=CostTier.FREE,
            rate_limits=RateLimits(requests_per_minute=30),
            best_for=["price_queries"],
            not_recommended_for=["on_chain_analysis"],
        )
    
    def test_metadata_creation(self):
        """Test creating metadata"""
        self.assertEqual(self.metadata.name, "TestSource")
        self.assertEqual(self.metadata.provider, "TestProvider")
        self.assertEqual(len(self.metadata.data_types), 2)
        self.assertEqual(len(self.metadata.capabilities), 2)
    
    def test_supports_data_type(self):
        """Test checking data type support"""
        self.assertTrue(self.metadata.supports_data_type(DataType.PRICE))
        self.assertTrue(self.metadata.supports_data_type(DataType.VOLUME))
        self.assertFalse(self.metadata.supports_data_type(DataType.ON_CHAIN))
    
    def test_has_capability(self):
        """Test checking capabilities"""
        self.assertTrue(self.metadata.has_capability(Capability.REAL_TIME))
        self.assertTrue(self.metadata.has_capability(Capability.HISTORICAL))
        self.assertFalse(self.metadata.has_capability(Capability.WHALE_TRACKING))
    
    def test_quality_score_calculation(self):
        """Test quality score algorithm"""
        score = self.metadata.quality_score(
            data_type=DataType.PRICE,
            required_capabilities=[Capability.REAL_TIME],
            priority_speed=True,
            priority_cost=False,
        )
        
        # Score should be high since we match requirements
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)
    
    def test_quality_score_no_match(self):
        """Test quality score when requirements don't match"""
        score = self.metadata.quality_score(
            data_type=DataType.ON_CHAIN,  # Not supported
            required_capabilities=[],
        )
        
        # Score should be very low
        self.assertEqual(score, 0.0)
    
    def test_quality_score_missing_capability(self):
        """Test quality score with missing capability"""
        score = self.metadata.quality_score(
            data_type=DataType.PRICE,
            required_capabilities=[Capability.WHALE_TRACKING],  # Not supported
        )
        
        # Score should be very low
        self.assertEqual(score, 0.0)
    
    def test_quality_score_speed_priority(self):
        """Test quality score with speed priority"""
        fast_metadata = DataSourceMetadata(
            name="Fast",
            provider="Test",
            description="Fast source",
            version="1.0",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            response_time=ResponseTime.REAL_TIME,
            reliability_score=0.9,
            cost_tier=CostTier.FREE,
        )
        
        slow_metadata = DataSourceMetadata(
            name="Slow",
            provider="Test",
            description="Slow source",
            version="1.0",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            response_time=ResponseTime.SLOW,
            reliability_score=0.9,
            cost_tier=CostTier.FREE,
        )
        
        fast_score = fast_metadata.quality_score(DataType.PRICE, priority_speed=True)
        slow_score = slow_metadata.quality_score(DataType.PRICE, priority_speed=True)
        
        self.assertGreater(fast_score, slow_score)
    
    def test_quality_score_cost_priority(self):
        """Test quality score with cost priority"""
        free_metadata = DataSourceMetadata(
            name="Free",
            provider="Test",
            description="Free source",
            version="1.0",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            response_time=ResponseTime.FAST,
            reliability_score=0.9,
            cost_tier=CostTier.FREE,
        )
        
        paid_metadata = DataSourceMetadata(
            name="Paid",
            provider="Test",
            description="Paid source",
            version="1.0",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            response_time=ResponseTime.FAST,
            reliability_score=0.9,
            cost_tier=CostTier.SUBSCRIPTION,
        )
        
        free_score = free_metadata.quality_score(DataType.PRICE, priority_cost=True)
        paid_score = paid_metadata.quality_score(DataType.PRICE, priority_cost=True)
        
        self.assertGreater(free_score, paid_score)
    
    def test_to_dict(self):
        """Test converting metadata to dict"""
        data = self.metadata.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data['name'], "TestSource")
        self.assertEqual(data['provider'], "TestProvider")
        self.assertIn('data_types', data)
        self.assertIn('capabilities', data)
    
    def test_to_openapi_operation(self):
        """Test generating OpenAPI operation"""
        operation = self.metadata.to_openapi_operation()
        
        self.assertIsInstance(operation, dict)
        self.assertIn('summary', operation)
        self.assertIn('operationId', operation)
        self.assertIn('parameters', operation)
        self.assertIn('responses', operation)
        
        # Check parameters
        params = operation['parameters']
        self.assertIsInstance(params, list)
        self.assertGreater(len(params), 0)


class TestResponseTime(unittest.TestCase):
    """Test ResponseTime enum"""
    
    def test_response_time_ordering(self):
        """Test that response times are ordered correctly"""
        times = [
            ResponseTime.REAL_TIME,
            ResponseTime.FAST,
            ResponseTime.MODERATE,
            ResponseTime.SLOW,
            ResponseTime.BATCH,
        ]
        
        # They should be in order of speed
        self.assertEqual(times[0].value, "real_time")
        self.assertEqual(times[-1].value, "batch")


class TestCostTier(unittest.TestCase):
    """Test CostTier enum"""
    
    def test_cost_tier_values(self):
        """Test cost tier values"""
        self.assertEqual(CostTier.FREE.value, "free")
        self.assertEqual(CostTier.FREEMIUM.value, "freemium")
        self.assertEqual(CostTier.SUBSCRIPTION.value, "subscription")
    
    def test_cost_tier_comparison(self):
        """Test that we have expected cost tiers"""
        tiers = [tier for tier in CostTier]
        self.assertIn(CostTier.FREE, tiers)
        self.assertIn(CostTier.PAID, tiers)


if __name__ == '__main__':
    unittest.main()
