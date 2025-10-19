"""
Glassnode data interface implementation.

Provides on-chain metrics and analytics from Glassnode API.
Requires paid API key for most features.
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    RateLimitError,
    AuthenticationError,
    DataNotAvailableError
)
from .metadata import (
    DataSourceMetadata,
    DataType,
    Capability,
    ResponseTime,
    CostTier,
    RateLimits
)

logger = logging.getLogger(__name__)


class GlassnodeInterface(DataInterface):
    """
    Glassnode API interface for on-chain metrics and analytics.
    
    Supports:
    - On-chain metrics (active addresses, transaction count, etc.)
    - Whale tracking and large holder analysis
    - Exchange flows (inflows/outflows)
    - Network health metrics
    - MVRV, SOPR, and other advanced metrics
    """
    
    BASE_URL = "https://api.glassnode.com/v1"
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.api_key = api_key or os.getenv('GLASSNODE_API_KEY')
        if not self.api_key:
            raise AuthenticationError("Glassnode API key is required")
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="Glassnode",
            provider="Glassnode",
            description="Premium on-chain analytics and metrics for Bitcoin and other cryptocurrencies",
            version="1.0.0",
            data_types=[
                DataType.ON_CHAIN,
                DataType.WHALE_TRANSACTIONS,
                DataType.EXCHANGE_FLOWS,
                DataType.NETWORK_METRICS,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.WHALE_TRACKING,
                Capability.EXCHANGE_MONITORING,
                Capability.TIME_SERIES,
                Capability.ADVANCED_ANALYTICS,
                Capability.RATE_LIMITED,
            ],
            response_time=ResponseTime.MODERATE,
            reliability_score=0.98,
            cost_tier=CostTier.SUBSCRIPTION,
            rate_limits=RateLimits(
                requests_per_minute=10,
                requests_per_hour=600,
                requests_per_day=10000,
            ),
            best_for=[
                "on_chain_analysis",
                "whale_tracking",
                "exchange_flow_monitoring",
                "network_health",
                "advanced_metrics",
                "hodl_waves",
            ],
            not_recommended_for=[
                "real_time_price",
                "social_sentiment",
                "news_aggregation",
            ],
            base_url=self.BASE_URL,
            requires_api_key=True,
            api_key_env_var="GLASSNODE_API_KEY",
            documentation_url="https://docs.glassnode.com/",
            data_freshness="10-minute delay",
            historical_data_available=True,
            historical_data_range="2009-present (varies by metric)",
            example_queries=[
                {
                    "description": "Get active addresses",
                    "request": {
                        "data_type": "on_chain",
                        "symbol": "BTC",
                        "parameters": {"metric": "addresses_active_count"}
                    }
                },
                {
                    "description": "Get whale transactions (>$1M)",
                    "request": {
                        "data_type": "whale_transactions",
                        "symbol": "BTC",
                        "parameters": {"threshold": 1000000}
                    }
                },
                {
                    "description": "Get exchange netflows",
                    "request": {
                        "data_type": "exchange_flows",
                        "symbol": "BTC",
                        "parameters": {"metric": "net_flows"}
                    }
                },
            ]
        )
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data from Glassnode API.
        
        Args:
            request: Data request
            
        Returns:
            Data response with on-chain metrics
        """
        start_time = datetime.now()
        
        try:
            await self.validate_request(request)
            await self._ensure_session()
            
            # Route to appropriate method based on data type
            if request.data_type == DataType.ON_CHAIN:
                data = await self._fetch_on_chain(request)
            elif request.data_type == DataType.WHALE_TRANSACTIONS:
                data = await self._fetch_whale_transactions(request)
            elif request.data_type == DataType.EXCHANGE_FLOWS:
                data = await self._fetch_exchange_flows(request)
            elif request.data_type == DataType.NETWORK_METRICS:
                data = await self._fetch_network_metrics(request)
            else:
                raise DataNotAvailableError(
                    f"Glassnode does not support data type: {request.data_type.value}"
                )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            self._call_count += 1
            
            return DataResponse(
                success=True,
                source="Glassnode",
                data=data,
                metadata={
                    'data_type': request.data_type.value,
                    'symbol': request.symbol,
                    'api_version': 'v1',
                    'data_delay': '10 minutes',
                },
                request_time=start_time,
                response_time=end_time,
                data_timestamp=datetime.now(),
                latency_ms=latency,
            )
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Glassnode fetch error: {e}")
            
            return DataResponse(
                success=False,
                source="Glassnode",
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_on_chain(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch on-chain metrics"""
        metric = request.parameters.get('metric', 'addresses_active_count')
        asset = request.symbol.lower()
        
        url = f"{self.BASE_URL}/metrics/addresses/{metric}"
        params = {
            'a': asset,
            'api_key': self.api_key,
        }
        
        # Add timeframe if specified
        if request.timeframe:
            params['since'] = self._get_since_timestamp(request.timeframe)
        
        async with self.session.get(url, params=params) as response:
            if response.status == 429:
                raise RateLimitError("Glassnode rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid Glassnode API key")
            
            response.raise_for_status()
            data = await response.json()
            
            return {
                'symbol': request.symbol,
                'metric': metric,
                'data': data,
                'count': len(data) if isinstance(data, list) else 1,
            }
    
    async def _fetch_whale_transactions(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch whale transaction data"""
        asset = request.symbol.lower()
        threshold = request.parameters.get('threshold', 1000000)
        
        # Use transactions_transfers_volume_sum metric
        url = f"{self.BASE_URL}/metrics/transactions/transfers_volume_sum"
        params = {
            'a': asset,
            'api_key': self.api_key,
        }
        
        if request.timeframe:
            params['since'] = self._get_since_timestamp(request.timeframe)
        
        async with self.session.get(url, params=params) as response:
            if response.status == 429:
                raise RateLimitError("Glassnode rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid Glassnode API key")
            
            response.raise_for_status()
            data = await response.json()
            
            # Filter for large transactions
            whale_txs = [
                tx for tx in data 
                if isinstance(tx, dict) and tx.get('v', 0) > threshold
            ]
            
            return {
                'symbol': request.symbol,
                'threshold': threshold,
                'whale_transactions': whale_txs,
                'count': len(whale_txs),
            }
    
    async def _fetch_exchange_flows(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch exchange flow data"""
        asset = request.symbol.lower()
        metric = request.parameters.get('metric', 'net_flows')
        
        # Map metric names
        metric_map = {
            'net_flows': 'transactions/transfers_volume_exchanges_net',
            'inflows': 'transactions/transfers_to_exchanges_count',
            'outflows': 'transactions/transfers_from_exchanges_count',
        }
        
        endpoint = metric_map.get(metric, metric)
        url = f"{self.BASE_URL}/metrics/{endpoint}"
        
        params = {
            'a': asset,
            'api_key': self.api_key,
        }
        
        if request.timeframe:
            params['since'] = self._get_since_timestamp(request.timeframe)
        
        async with self.session.get(url, params=params) as response:
            if response.status == 429:
                raise RateLimitError("Glassnode rate limit exceeded")
            elif response.status == 401:
                raise AuthenticationError("Invalid Glassnode API key")
            
            response.raise_for_status()
            data = await response.json()
            
            return {
                'symbol': request.symbol,
                'metric': metric,
                'data': data,
                'count': len(data) if isinstance(data, list) else 1,
            }
    
    async def _fetch_network_metrics(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch network health metrics"""
        asset = request.symbol.lower()
        
        # Fetch multiple network metrics
        metrics = [
            'blockchain/block_count',
            'blockchain/block_interval_mean',
            'mining/difficulty_latest',
            'mining/hash_rate_mean',
        ]
        
        results = {}
        for metric in metrics:
            url = f"{self.BASE_URL}/metrics/{metric}"
            params = {
                'a': asset,
                'api_key': self.api_key,
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    metric_name = metric.split('/')[-1]
                    results[metric_name] = data
        
        return {
            'symbol': request.symbol,
            'metrics': results,
        }
    
    def _get_since_timestamp(self, timeframe: str) -> int:
        """Convert timeframe to Unix timestamp"""
        # Parse timeframe like "7d", "30d", "1y"
        if timeframe.endswith('d'):
            days = int(timeframe[:-1])
            since = datetime.now() - timedelta(days=days)
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            since = datetime.now() - timedelta(hours=hours)
        elif timeframe.endswith('y'):
            years = int(timeframe[:-1])
            since = datetime.now() - timedelta(days=years * 365)
        else:
            since = datetime.now() - timedelta(days=30)
        
        return int(since.timestamp())
    
    async def health_check(self) -> bool:
        """Check if Glassnode API is available"""
        try:
            await self._ensure_session()
            
            # Simple ping using a lightweight endpoint
            url = f"{self.BASE_URL}/metrics/market/price_usd_close"
            params = {
                'a': 'BTC',
                'api_key': self.api_key,
            }
            
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Glassnode health check failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session') and self.session:
            try:
                asyncio.create_task(self._close_session())
            except RuntimeError:
                pass  # Event loop may be closed
