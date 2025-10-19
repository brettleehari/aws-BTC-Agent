"""
Base interface for data sources with capability advertisement.

All data source implementations must inherit from DataInterface
and provide their metadata for capability discovery.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from .metadata import DataSourceMetadata, DataType


class RequestPriority(Enum):
    """Priority level for data requests"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DataRequest:
    """
    Standardized data request format.
    
    All data sources accept this common request format,
    ensuring consistency across different providers.
    """
    
    # What data is being requested
    data_type: DataType
    symbol: str = "BTC"
    
    # Time parameters
    timeframe: Optional[str] = None  # e.g., "1h", "24h", "7d"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Request metadata
    request_id: Optional[str] = None
    priority: RequestPriority = RequestPriority.NORMAL
    timeout: int = 30  # seconds
    
    # Source-specific parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Cache control
    use_cache: bool = True
    cache_ttl: Optional[int] = None  # seconds
    
    def to_dict(self) -> Dict:
        """Convert request to dictionary"""
        return {
            'data_type': self.data_type.value if isinstance(self.data_type, DataType) else self.data_type,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'request_id': self.request_id,
            'priority': self.priority.value,
            'timeout': self.timeout,
            'parameters': self.parameters,
            'use_cache': self.use_cache,
            'cache_ttl': self.cache_ttl,
        }


@dataclass
class DataResponse:
    """
    Standardized data response format.
    
    All data sources return this common response format,
    making it easy to work with data from different providers.
    """
    
    # Response status
    success: bool
    source: str
    
    # Data payload
    data: Dict[str, Any]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    request_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    data_timestamp: Optional[datetime] = None
    
    # Error information (if success=False)
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Cache information
    from_cache: bool = False
    cache_age: Optional[int] = None  # seconds
    
    # Performance metrics
    latency_ms: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert response to dictionary"""
        return {
            'success': self.success,
            'source': self.source,
            'data': self.data,
            'metadata': self.metadata,
            'request_time': self.request_time.isoformat() if self.request_time else None,
            'response_time': self.response_time.isoformat() if self.response_time else None,
            'data_timestamp': self.data_timestamp.isoformat() if self.data_timestamp else None,
            'error': self.error,
            'error_code': self.error_code,
            'from_cache': self.from_cache,
            'cache_age': self.cache_age,
            'latency_ms': self.latency_ms,
        }


class DataInterface(ABC):
    """
    Abstract base class for all data source interfaces.
    
    Each data source implementation must:
    1. Provide metadata describing its capabilities
    2. Implement the fetch() method to retrieve data
    3. Implement quality scoring for intelligent routing
    4. Handle errors and rate limiting gracefully
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        """
        Initialize data interface.
        
        Args:
            api_key: Optional API key for authenticated sources
            config: Optional configuration dictionary
        """
        self.api_key = api_key
        self.config = config or {}
        self._call_count = 0
        self._error_count = 0
        self._last_error = None
    
    @property
    @abstractmethod
    def metadata(self) -> DataSourceMetadata:
        """
        Return metadata describing this data source's capabilities.
        
        This metadata is used by agents to discover and select
        appropriate data sources for their needs.
        """
        pass
    
    @abstractmethod
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data based on the request.
        
        Args:
            request: Standardized data request
            
        Returns:
            Standardized data response
            
        Raises:
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If API key is invalid
            DataNotAvailableError: If requested data doesn't exist
            TimeoutError: If request times out
        """
        pass
    
    def can_handle(self, request: DataRequest) -> bool:
        """
        Check if this data source can handle the request.
        
        Args:
            request: Data request to evaluate
            
        Returns:
            True if this source supports the requested data type
        """
        return self.metadata.supports_data_type(request.data_type)
    
    def quality_score(self, request: DataRequest) -> float:
        """
        Calculate quality score (0-1) for handling this request.
        
        Higher scores indicate this source is better suited
        for the specific request.
        
        Args:
            request: Data request to evaluate
            
        Returns:
            Score from 0 (unsuitable) to 1 (perfect match)
        """
        requirements = {
            'data_type': request.data_type,
            'speed': 'critical' if request.priority == RequestPriority.CRITICAL else 'normal',
        }
        return self.metadata.quality_score(requirements)
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the data source is available and healthy.
        
        Returns:
            True if source is healthy and responsive
        """
        pass
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        return {
            'rate_limits': self.metadata.rate_limits,
            'call_count': self._call_count,
            'error_count': self._error_count,
            'last_error': self._last_error,
        }
    
    async def validate_request(self, request: DataRequest) -> bool:
        """
        Validate that the request can be fulfilled.
        
        Args:
            request: Request to validate
            
        Returns:
            True if request is valid
            
        Raises:
            ValueError: If request is invalid
        """
        if not self.can_handle(request):
            raise ValueError(
                f"{self.metadata.name} cannot handle data type {request.data_type.value}"
            )
        
        if self.metadata.requires_api_key and not self.api_key:
            raise ValueError(
                f"{self.metadata.name} requires an API key. "
                f"Set {self.metadata.api_key_env_var} environment variable."
            )
        
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.metadata.name}, provider={self.metadata.provider})"


# Custom exceptions for data interface operations
class DataInterfaceError(Exception):
    """Base exception for data interface errors"""
    pass


class RateLimitError(DataInterfaceError):
    """Raised when rate limit is exceeded"""
    pass


class AuthenticationError(DataInterfaceError):
    """Raised when authentication fails"""
    pass


class DataNotAvailableError(DataInterfaceError):
    """Raised when requested data is not available"""
    pass


class TimeoutError(DataInterfaceError):
    """Raised when request times out"""
    pass
