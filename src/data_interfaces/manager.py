"""
Data Interface Manager for intelligent orchestration of multiple data sources.

Provides unified access to all data interfaces with:
- Automatic source selection based on quality scores
- Fallback mechanism when primary source fails
- Parallel fetching for redundancy
- Caching layer integration
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    DataNotAvailableError
)
from .registry import CapabilityRegistry, get_registry
from .metadata import DataType, Capability

logger = logging.getLogger(__name__)


class DataInterfaceManager:
    """
    Manager for coordinating multiple data interfaces.
    
    Features:
    - Intelligent source selection based on requirements
    - Automatic fallback to alternative sources
    - Parallel fetching with fastest-wins strategy
    - Health monitoring and circuit breaking
    - Response caching
    """
    
    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        enable_fallback: bool = True,
        enable_parallel: bool = False,
        cache_ttl: int = 60,
    ):
        """
        Initialize manager.
        
        Args:
            registry: Capability registry (uses global if not provided)
            enable_fallback: Enable automatic fallback to alternative sources
            enable_parallel: Enable parallel fetching from multiple sources
            cache_ttl: Cache time-to-live in seconds
        """
        self.registry = registry or get_registry()
        self.enable_fallback = enable_fallback
        self.enable_parallel = enable_parallel
        self.cache_ttl = cache_ttl
        self.cache: Dict[str, tuple[DataResponse, datetime]] = {}
        
        # Track source health
        self.circuit_breaker: Dict[str, dict] = {}
    
    async def fetch(
        self,
        request: DataRequest,
        preferred_source: Optional[str] = None,
        use_cache: bool = True,
    ) -> DataResponse:
        """
        Fetch data using the best available source.
        
        Args:
            request: Data request
            preferred_source: Preferred source name (optional)
            use_cache: Whether to use cached responses
            
        Returns:
            Data response
        """
        # Check cache first
        if use_cache and request.use_cache:
            cached = self._get_cached(request)
            if cached:
                logger.info(f"Cache hit for {request.data_type.value}")
                return cached
        
        # Get ranked sources
        sources = self.registry.get_source_rankings(request)
        
        if not sources:
            return DataResponse(
                success=False,
                source="DataInterfaceManager",
                data={},
                error=f"No sources available for data type: {request.data_type.value}",
                error_code="NO_SOURCES_AVAILABLE",
                request_time=datetime.now(),
                response_time=datetime.now(),
            )
        
        # If preferred source specified, try it first
        if preferred_source:
            sources = sorted(
                sources,
                key=lambda x: (x[0] != preferred_source, -x[1])
            )
        
        # Try parallel fetching if enabled
        if self.enable_parallel and len(sources) > 1:
            response = await self._fetch_parallel(request, sources[:3])
            if response.success:
                self._cache_response(request, response)
                return response
        
        # Sequential fetching with fallback
        for source_name, score in sources:
            source_info = (source_name, score)
            
            # Check circuit breaker
            if self._is_circuit_open(source_name):
                logger.warning(f"Circuit breaker open for {source_name}, skipping")
                continue
            
            try:
                source = self.registry.create_source_instance(source_name)
                logger.info(f"Fetching from {source_name} (score: {score:.2f})")
                
                response = await source.fetch(request)
                
                if response.success:
                    self._record_success(source_name)
                    self._cache_response(request, response)
                    return response
                else:
                    self._record_failure(source_name)
                    logger.warning(f"{source_name} failed: {response.error}")
                    
                    if not self.enable_fallback:
                        return response
                        
            except Exception as e:
                self._record_failure(source_name)
                logger.error(f"Error fetching from {source_name}: {e}")
                
                if not self.enable_fallback:
                    return DataResponse(
                        success=False,
                        source=source_name,
                        data={},
                        error=str(e),
                        error_code=type(e).__name__,
                        request_time=datetime.now(),
                        response_time=datetime.now(),
                    )
        
        # All sources failed
        return DataResponse(
            success=False,
            source="DataInterfaceManager",
            data={},
            error="All data sources failed or unavailable",
            error_code="ALL_SOURCES_FAILED",
            request_time=datetime.now(),
            response_time=datetime.now(),
        )
    
    async def _fetch_parallel(
        self,
        request: DataRequest,
        sources: List[Dict[str, Any]],
    ) -> DataResponse:
        """
        Fetch from multiple sources in parallel, return first success.
        
        Args:
            request: Data request
            sources: List of source info dicts
            
        Returns:
            First successful response
        """
        async def fetch_from_source(source_info: Dict[str, Any]) -> DataResponse:
            """Wrapper for fetching from a single source"""
            source_name = source_info['name']
            
            if self._is_circuit_open(source_name):
                return DataResponse(
                    success=False,
                    source=source_name,
                    data={},
                    error="Circuit breaker open",
                    error_code="CIRCUIT_OPEN",
                    request_time=datetime.now(),
                    response_time=datetime.now(),
                )
            
            try:
                source = self.registry.create_source_instance(source_name)
                response = await source.fetch(request)
                
                if response.success:
                    self._record_success(source_name)
                else:
                    self._record_failure(source_name)
                
                return response
                
            except Exception as e:
                self._record_failure(source_name)
                return DataResponse(
                    success=False,
                    source=source_name,
                    data={},
                    error=str(e),
                    error_code=type(e).__name__,
                    request_time=datetime.now(),
                    response_time=datetime.now(),
                )
        
        # Fetch from all sources in parallel
        tasks = [fetch_from_source(source) for source in sources]
        
        # Wait for first success or all failures
        for coro in asyncio.as_completed(tasks):
            response = await coro
            if response.success:
                logger.info(f"Parallel fetch succeeded with {response.source}")
                return response
        
        # All failed
        return DataResponse(
            success=False,
            source="DataInterfaceManager",
            data={},
            error="All parallel fetches failed",
            error_code="ALL_PARALLEL_FAILED",
            request_time=datetime.now(),
            response_time=datetime.now(),
        )
    
    def _get_cached(self, request: DataRequest) -> Optional[DataResponse]:
        """Get cached response if available and not expired"""
        cache_key = self._get_cache_key(request)
        
        if cache_key in self.cache:
            response, cached_at = self.cache[cache_key]
            age = (datetime.now() - cached_at).total_seconds()
            
            if age < self.cache_ttl:
                response.cached = True
                response.cache_age = age
                return response
            else:
                # Expired, remove from cache
                del self.cache[cache_key]
        
        return None
    
    def _cache_response(self, request: DataRequest, response: DataResponse):
        """Cache a successful response"""
        if response.success:
            cache_key = self._get_cache_key(request)
            self.cache[cache_key] = (response, datetime.now())
    
    def _get_cache_key(self, request: DataRequest) -> str:
        """Generate cache key for request"""
        params_str = '_'.join(f"{k}={v}" for k, v in sorted(request.parameters.items()))
        return f"{request.data_type.value}_{request.symbol}_{request.timeframe}_{params_str}"
    
    def _is_circuit_open(self, source_name: str) -> bool:
        """Check if circuit breaker is open for source"""
        if source_name not in self.circuit_breaker:
            return False
        
        breaker = self.circuit_breaker[source_name]
        
        # Circuit opens after 5 consecutive failures
        if breaker['consecutive_failures'] >= 5:
            # Stay open for 60 seconds
            time_since_open = (datetime.now() - breaker['opened_at']).total_seconds()
            if time_since_open < 60:
                return True
            else:
                # Try half-open state
                breaker['consecutive_failures'] = 0
                return False
        
        return False
    
    def _record_success(self, source_name: str):
        """Record successful fetch from source"""
        if source_name in self.circuit_breaker:
            self.circuit_breaker[source_name]['consecutive_failures'] = 0
    
    def _record_failure(self, source_name: str):
        """Record failed fetch from source"""
        if source_name not in self.circuit_breaker:
            self.circuit_breaker[source_name] = {
                'consecutive_failures': 0,
                'total_failures': 0,
                'opened_at': None,
            }
        
        breaker = self.circuit_breaker[source_name]
        breaker['consecutive_failures'] += 1
        breaker['total_failures'] += 1
        
        if breaker['consecutive_failures'] >= 5:
            breaker['opened_at'] = datetime.now()
            logger.warning(f"Circuit breaker opened for {source_name}")
    
    def clear_cache(self):
        """Clear all cached responses"""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def reset_circuit_breakers(self):
        """Reset all circuit breakers"""
        self.circuit_breaker.clear()
        logger.info("Circuit breakers reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get manager status and statistics"""
        return {
            'cache_size': len(self.cache),
            'cache_ttl': self.cache_ttl,
            'enable_fallback': self.enable_fallback,
            'enable_parallel': self.enable_parallel,
            'circuit_breakers': {
                name: {
                    'consecutive_failures': info['consecutive_failures'],
                    'total_failures': info['total_failures'],
                    'is_open': self._is_circuit_open(name),
                }
                for name, info in self.circuit_breaker.items()
            },
            'registered_sources': len(self.registry.list_sources()),
        }


# Global manager instance
_manager: Optional[DataInterfaceManager] = None


def get_manager(cache_ttl: int = 60, enable_fallback: bool = True, enable_parallel: bool = False) -> DataInterfaceManager:
    """Get global manager instance with optional configuration"""
    global _manager
    if _manager is None:
        _manager = DataInterfaceManager(
            cache_ttl=cache_ttl,
            enable_fallback=enable_fallback,
            enable_parallel=enable_parallel
        )
    return _manager


def reset_manager():
    """Reset global manager instance"""
    global _manager
    _manager = None
