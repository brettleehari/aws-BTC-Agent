"""
Test suite for base interface and request/response models.
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.data_interfaces.base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    RequestPriority,
    DataInterfaceError,
    RateLimitError,
    AuthenticationError,
    DataNotAvailableError,
    TimeoutError,
)
from src.data_interfaces.metadata import DataType, Capability


class TestRequestPriority(unittest.TestCase):
    """Test RequestPriority enum"""
    
    def test_priority_values(self):
        """Test priority values"""
        self.assertEqual(RequestPriority.LOW.value, "low")
        self.assertEqual(RequestPriority.NORMAL.value, "normal")
        self.assertEqual(RequestPriority.HIGH.value, "high")
        self.assertEqual(RequestPriority.CRITICAL.value, "critical")


class TestDataRequest(unittest.TestCase):
    """Test DataRequest dataclass"""
    
    def test_basic_request(self):
        """Test creating basic request"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        self.assertEqual(request.data_type, DataType.PRICE)
        self.assertEqual(request.symbol, "BTC")
        self.assertIsNone(request.timeframe)
        self.assertEqual(request.parameters, {})
        self.assertEqual(request.priority, RequestPriority.NORMAL)
    
    def test_full_request(self):
        """Test creating request with all fields"""
        request = DataRequest(
            data_type=DataType.ON_CHAIN,
            symbol="BTC",
            timeframe="7d",
            parameters={"metric": "active_addresses"},
            priority=RequestPriority.HIGH,
            cache_enabled=False,
            timeout=30.0,
        )
        
        self.assertEqual(request.data_type, DataType.ON_CHAIN)
        self.assertEqual(request.symbol, "BTC")
        self.assertEqual(request.timeframe, "7d")
        self.assertEqual(request.parameters["metric"], "active_addresses")
        self.assertEqual(request.priority, RequestPriority.HIGH)
        self.assertFalse(request.cache_enabled)
        self.assertEqual(request.timeout, 30.0)


class TestDataResponse(unittest.TestCase):
    """Test DataResponse dataclass"""
    
    def test_successful_response(self):
        """Test successful response"""
        now = datetime.now()
        response = DataResponse(
            success=True,
            source="TestSource",
            data={"price": 50000},
            metadata={"currency": "USD"},
            request_time=now,
            response_time=now,
            data_timestamp=now,
            latency_ms=100.5,
        )
        
        self.assertTrue(response.success)
        self.assertEqual(response.source, "TestSource")
        self.assertEqual(response.data["price"], 50000)
        self.assertEqual(response.metadata["currency"], "USD")
        self.assertEqual(response.latency_ms, 100.5)
        self.assertIsNone(response.error)
        self.assertFalse(response.cached)
    
    def test_failed_response(self):
        """Test failed response"""
        now = datetime.now()
        response = DataResponse(
            success=False,
            source="TestSource",
            data={},
            error="Rate limit exceeded",
            error_code="RATE_LIMIT",
            request_time=now,
            response_time=now,
        )
        
        self.assertFalse(response.success)
        self.assertEqual(response.error, "Rate limit exceeded")
        self.assertEqual(response.error_code, "RATE_LIMIT")
    
    def test_cached_response(self):
        """Test cached response"""
        now = datetime.now()
        response = DataResponse(
            success=True,
            source="TestSource",
            data={"price": 50000},
            request_time=now,
            response_time=now,
            cached=True,
            cache_age=30.0,
        )
        
        self.assertTrue(response.cached)
        self.assertEqual(response.cache_age, 30.0)


class TestExceptions(unittest.TestCase):
    """Test custom exceptions"""
    
    def test_base_exception(self):
        """Test base exception"""
        error = DataInterfaceError("Test error")
        self.assertEqual(str(error), "Test error")
        self.assertIsInstance(error, Exception)
    
    def test_rate_limit_error(self):
        """Test rate limit error"""
        error = RateLimitError("Rate limit exceeded")
        self.assertIsInstance(error, DataInterfaceError)
    
    def test_authentication_error(self):
        """Test authentication error"""
        error = AuthenticationError("Invalid API key")
        self.assertIsInstance(error, DataInterfaceError)
    
    def test_data_not_available_error(self):
        """Test data not available error"""
        error = DataNotAvailableError("Data not found")
        self.assertIsInstance(error, DataInterfaceError)
    
    def test_timeout_error(self):
        """Test timeout error"""
        error = TimeoutError("Request timed out")
        self.assertIsInstance(error, DataInterfaceError)


class MockDataInterface(DataInterface):
    """Mock implementation for testing"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_called = False
        self.health_check_called = False
    
    @property
    def metadata(self):
        from src.data_interfaces.metadata import DataSourceMetadata, ResponseTime, CostTier
        return DataSourceMetadata(
            name="MockSource",
            provider="Test",
            description="Mock data source",
            version="1.0.0",
            data_types=[DataType.PRICE],
            capabilities=[Capability.REAL_TIME],
            response_time=ResponseTime.FAST,
            reliability_score=0.95,
            cost_tier=CostTier.FREE,
        )
    
    async def fetch(self, request):
        self.fetch_called = True
        return DataResponse(
            success=True,
            source="MockSource",
            data={"price": 50000},
            request_time=datetime.now(),
            response_time=datetime.now(),
        )
    
    async def health_check(self):
        self.health_check_called = True
        return True


class TestDataInterface(unittest.TestCase):
    """Test DataInterface abstract base class"""
    
    def setUp(self):
        """Set up test interface"""
        self.interface = MockDataInterface()
    
    def test_interface_creation(self):
        """Test creating interface"""
        self.assertIsInstance(self.interface, DataInterface)
        self.assertIsNotNone(self.interface.metadata)
    
    def test_can_handle(self):
        """Test can_handle method"""
        self.assertTrue(self.interface.can_handle(DataType.PRICE))
        self.assertFalse(self.interface.can_handle(DataType.ON_CHAIN))
    
    def test_quality_score(self):
        """Test quality_score method"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        score = self.interface.quality_score(request)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)
    
    def test_quality_score_unsupported(self):
        """Test quality score for unsupported data type"""
        request = DataRequest(
            data_type=DataType.ON_CHAIN,
            symbol="BTC",
        )
        
        score = self.interface.quality_score(request)
        self.assertEqual(score, 0.0)
    
    def test_validate_request_valid(self):
        """Test validating valid request"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        # Should not raise exception
        asyncio.run(self.interface.validate_request(request))
    
    def test_validate_request_missing_symbol(self):
        """Test validating request with missing symbol"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="",  # Empty symbol
        )
        
        with self.assertRaises(ValueError):
            asyncio.run(self.interface.validate_request(request))
    
    def test_fetch(self):
        """Test fetch method"""
        request = DataRequest(
            data_type=DataType.PRICE,
            symbol="BTC",
        )
        
        response = asyncio.run(self.interface.fetch(request))
        
        self.assertTrue(self.interface.fetch_called)
        self.assertIsInstance(response, DataResponse)
        self.assertTrue(response.success)
    
    def test_health_check(self):
        """Test health check"""
        result = asyncio.run(self.interface.health_check())
        
        self.assertTrue(self.interface.health_check_called)
        self.assertTrue(result)
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status"""
        status = self.interface.get_rate_limit_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('calls_made', status)
        self.assertIn('errors', status)
        self.assertIn('last_call', status)
        self.assertIn('last_error', status)


class TestDataInterfaceWithConfig(unittest.TestCase):
    """Test DataInterface with configuration"""
    
    def test_interface_with_api_key(self):
        """Test creating interface with API key"""
        interface = MockDataInterface(api_key="test_key_123")
        self.assertEqual(interface.api_key, "test_key_123")
    
    def test_interface_with_config(self):
        """Test creating interface with config"""
        config = {
            'timeout': 30,
            'retry_count': 3,
        }
        interface = MockDataInterface(config=config)
        self.assertEqual(interface.config, config)
    
    def test_interface_no_credentials(self):
        """Test creating interface without credentials"""
        interface = MockDataInterface()
        self.assertIsNone(interface.api_key)
        self.assertEqual(interface.config, {})


if __name__ == '__main__':
    unittest.main()
