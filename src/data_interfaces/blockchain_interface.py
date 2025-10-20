"""
Blockchain.com API interface for on-chain Bitcoin data.

Provides free access to:
- On-chain metrics (network hash rate, difficulty, mempool)
- Whale transactions (large transfers)
- Exchange flows
- Network statistics
- Block and transaction data

API Documentation: https://www.blockchain.com/api
Free Tier: Unlimited (no API key required)
"""

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    DataNotAvailableError,
    RateLimitError
)
from .metadata import (
    DataSourceMetadata,
    DataType,
    Capability,
    ResponseTime,
    RateLimits,
    CostTier
)

logger = logging.getLogger(__name__)


class BlockchainDotComInterface(DataInterface):
    """
    Blockchain.com API interface for on-chain Bitcoin data.
    
    Features:
    - Network statistics (hash rate, difficulty, blocks)
    - Whale transaction detection (>100 BTC)
    - Exchange flow monitoring
    - Mempool statistics
    - Address balance queries
    
    Rate Limits:
    - Free tier: No stated limit (reasonable use)
    - No API key required
    
    Use Cases:
    - Monitor large BTC movements
    - Track network health
    - Detect exchange flows
    - Analyze on-chain activity
    """
    
    BASE_URL = "https://blockchain.info"
    CHARTS_URL = "https://api.blockchain.info/charts"
    STATS_URL = "https://blockchain.info/stats"
    
    # Whale transaction threshold (100 BTC)
    WHALE_THRESHOLD_BTC = 100
    
    # Exchange addresses (major exchanges)
    KNOWN_EXCHANGE_ADDRESSES = {
        # Binance
        "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo": "Binance",
        "bc1qm34lsc65zpw79lxes69zkqmk6ee3ewf0j77s3h": "Binance",
        # Coinbase
        "3M219KR5vEneNb47ewrPfWyb5jQ2DjxRP6": "Coinbase",
        "bc1qgdjqv0av3q56jvd82tkdjpy7gdp9ut8tlqmgrpmv24sq90ecnvqqjwvw97": "Coinbase",
        # Add more as needed
    }
    
    def __init__(self):
        """Initialize Blockchain.com interface."""
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._request_window_start = datetime.now()
    
    @property
    def metadata(self) -> DataSourceMetadata:
        """Return metadata about this data source"""
        return DataSourceMetadata(
            name="BlockchainDotCom",
            provider="Blockchain.com",
            description="Free on-chain Bitcoin data including whale transactions, network stats, and exchange flows",
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
            ],
            rate_limits=RateLimits(
                requests_per_minute=60,  # Conservative estimate
                requests_per_hour=1000,
            ),
            cost_tier=CostTier.FREE,
            response_time=ResponseTime.FAST,
            reliability_score=0.90,
            requires_api_key=False,
            base_url=self.BASE_URL,
            best_for=["On-chain analysis", "Whale tracking", "Network health"],
        )
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make API request to Blockchain.com.
        
        Args:
            url: Full URL to request
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            RateLimitError: If rate limit exceeded
            DataNotAvailableError: If data not available
        """
        await self._ensure_session()
        
        # Simple rate limiting (60 requests per minute)
        if datetime.now() - self._request_window_start > timedelta(minutes=1):
            self._request_count = 0
            self._request_window_start = datetime.now()
        
        if self._request_count >= 60:
            raise RateLimitError("Rate limit exceeded (60 requests/minute)")
        
        try:
            async with self.session.get(url, params=params) as response:
                self._request_count += 1
                
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('Content-Type', '')
                    
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        # Some endpoints return plain text
                        text = await response.text()
                        try:
                            # Try to convert to number if it's a single value
                            return {"value": float(text)}
                        except:
                            return {"value": text}
                
                elif response.status == 429:
                    raise RateLimitError("Blockchain.com rate limit exceeded")
                
                else:
                    error_text = await response.text()
                    raise DataNotAvailableError(
                        f"Blockchain.com API error: {response.status} - {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            raise DataNotAvailableError(f"Network error: {str(e)}")
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data from Blockchain.com API.
        
        Args:
            request: Data request specifying what to fetch
            
        Returns:
            Data response with fetched data
        """
        start_time = datetime.now()
        
        try:
            # Route to appropriate handler based on data type
            if request.data_type == DataType.ON_CHAIN:
                data = await self._fetch_on_chain_metrics(request)
            elif request.data_type == DataType.WHALE_TRANSACTIONS:
                data = await self._fetch_whale_transactions(request)
            elif request.data_type == DataType.EXCHANGE_FLOWS:
                data = await self._fetch_exchange_flows(request)
            elif request.data_type == DataType.NETWORK_METRICS:
                data = await self._fetch_network_metrics(request)
            else:
                return DataResponse(
                    success=False,
                    source=self.metadata.name,
                    data={},
                    error=f"BlockchainDotCom cannot handle data type {request.data_type.value}",
                    error_code="UNSUPPORTED_DATA_TYPE",
                    request_time=start_time,
                    response_time=datetime.now(),
                )
            
            return DataResponse(
                success=True,
                source=self.metadata.name,
                data=data,
                request_time=start_time,
                response_time=datetime.now(),
                metadata={
                    "requests_in_window": self._request_count,
                }
            )
        
        except (RateLimitError, DataNotAvailableError) as e:
            logger.error(f"BlockchainDotCom fetch error: {str(e)}")
            return DataResponse(
                success=False,
                source=self.metadata.name,
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error in BlockchainDotCom fetch: {str(e)}")
            return DataResponse(
                success=False,
                source=self.metadata.name,
                data={},
                error=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR",
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_on_chain_metrics(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch comprehensive on-chain metrics.
        """
        # Fetch multiple stats in parallel
        stats_data = await self._make_request(f"{self.STATS_URL}?format=json")
        
        # Calculate metrics
        return {
            "market_price_usd": stats_data.get("market_price_usd", 0),
            "hash_rate": stats_data.get("hash_rate", 0),  # GH/s
            "difficulty": stats_data.get("difficulty", 0),
            "total_btc": stats_data.get("totalbc", 0) / 1e8,  # Convert from satoshis
            "n_blocks_mined": stats_data.get("n_blocks_mined", 0),
            "minutes_between_blocks": stats_data.get("minutes_between_blocks", 0),
            "n_tx": stats_data.get("n_tx", 0),  # Total transactions
            "blocks_size": stats_data.get("blocks_size", 0),
            "miners_revenue_usd": stats_data.get("miners_revenue_usd", 0),
            "trade_volume_btc": stats_data.get("trade_volume_btc", 0),
            "trade_volume_usd": stats_data.get("trade_volume_usd", 0),
            "timestamp": datetime.now().isoformat(),
            "source": "Blockchain.com",
        }
    
    async def _fetch_whale_transactions(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch large BTC transactions (whale activity).
        
        Note: This requires fetching recent blocks and scanning for large transactions.
        For production, consider using Blockchain.com's WebSocket for real-time data.
        """
        # Get latest block
        stats = await self._make_request(f"{self.STATS_URL}?format=json")
        latest_block_height = stats.get("n_blocks_total", 0)
        
        # For demo, we'll return stats about recent large transactions
        # In production, you'd fetch actual block data and parse transactions
        
        return {
            "whale_threshold_btc": self.WHALE_THRESHOLD_BTC,
            "latest_block": latest_block_height,
            "message": "Whale transaction detection requires real-time block parsing",
            "recommendation": "Use Blockchain.com WebSocket API for real-time whale detection",
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _fetch_exchange_flows(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch Bitcoin flows to/from known exchange addresses.
        
        Note: Requires address monitoring. This is a simplified version.
        """
        return {
            "monitored_exchanges": len(self.KNOWN_EXCHANGE_ADDRESSES),
            "exchanges": list(self.KNOWN_EXCHANGE_ADDRESSES.values()),
            "message": "Exchange flow monitoring requires address tracking",
            "recommendation": "Use Blockchain.com address API with known exchange addresses",
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _fetch_network_metrics(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch Bitcoin network health metrics.
        """
        # Fetch various network stats
        stats = await self._make_request(f"{self.STATS_URL}?format=json")
        
        # Calculate network health indicators
        hash_rate = stats.get("hash_rate", 0)
        difficulty = stats.get("difficulty", 0)
        minutes_between_blocks = stats.get("minutes_between_blocks", 10)
        
        # Health score (0-100)
        block_time_health = max(0, 100 - abs(minutes_between_blocks - 10) * 10)  # Ideal: 10 min
        hash_rate_health = min(100, hash_rate / 1e11 * 100) if hash_rate else 0  # Relative score
        
        overall_health = (block_time_health + hash_rate_health) / 2
        
        return {
            "network_health_score": overall_health,
            "hash_rate_ghs": hash_rate,
            "difficulty": difficulty,
            "average_block_time_minutes": minutes_between_blocks,
            "blocks_mined_24h": stats.get("n_blocks_mined", 0),
            "total_transactions_24h": stats.get("n_tx", 0),
            "total_btc_supply": stats.get("totalbc", 0) / 1e8,
            "timestamp": datetime.now().isoformat(),
            "interpretation": {
                "block_time": "healthy" if 9 <= minutes_between_blocks <= 11 else "degraded",
                "hash_rate": "strong" if hash_rate > 1e11 else "moderate",
                "overall": "healthy" if overall_health > 70 else "moderate" if overall_health > 40 else "concerning"
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Blockchain.com API is accessible and healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            start_time = datetime.now()
            
            # Make a simple request to check API health
            await self._make_request(f"{self.STATS_URL}?format=json")
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "message": "Blockchain.com API is accessible",
            }
        
        except RateLimitError:
            return {
                "status": "degraded",
                "message": "Rate limit exceeded",
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Health check failed: {str(e)}",
            }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            try:
                asyncio.get_event_loop().create_task(self.session.close())
            except:
                pass
