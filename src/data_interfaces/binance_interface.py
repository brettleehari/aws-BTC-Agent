"""
Binance API interface for real-time cryptocurrency market data.

Provides high-frequency price feeds, order book data, trade streams,
and 24-hour statistics from the world's largest crypto exchange.

API Documentation: https://binance-docs.github.io/apidocs/spot/en/
Rate Limits: 1200 requests/minute, 6000 requests/5 minutes (no API key required)
Public Data: Free access to all market data endpoints
"""

import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    DataNotAvailableError,
    RateLimitError,
    AuthenticationError
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


class BinanceInterface(DataInterface):
    """
    Binance API interface for real-time cryptocurrency market data.
    
    Features:
    - Real-time price feeds (sub-second latency)
    - 24-hour price statistics (high, low, volume, change)
    - Order book depth (bids/asks up to 5000 levels)
    - Recent trades stream
    - Historical kline/candlestick data
    - Exchange status and system health
    
    Rate Limits:
    - 1200 requests/minute (weight-based system)
    - 6000 requests/5 minutes
    - No API key required for public data
    
    Use Cases:
    - Real-time price monitoring
    - Order book analysis
    - Trade flow analysis
    - Volume analysis
    - Cross-exchange arbitrage detection
    """
    
    # Use Binance.US for US-based access (or set via environment variable)
    BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.us")
    
    # Symbol mapping (Binance uses uppercase pairs with no separator)
    SYMBOL_MAPPING = {
        "BTC": "BTCUSDT",
        "ETH": "ETHUSDT",
        "BNB": "BNBUSDT",
        "XRP": "XRPUSDT",
        "ADA": "ADAUSDT",
        "SOL": "SOLUSDT",
        "DOGE": "DOGEUSDT",
    }
    
    # Default symbol for BTC
    DEFAULT_SYMBOL = "BTCUSDT"
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        """
        Initialize Binance interface.
        
        Args:
            api_key: Binance API key (optional, only needed for private endpoints)
            api_secret: Binance API secret (optional, only needed for private endpoints)
        
        Note: Public market data does not require authentication.
        """
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        
        # Rate limiting tracking (weight-based system)
        self._request_count_minute = 0
        self._request_count_5min = 0
        self._minute_reset_time = datetime.now()
        self._5min_reset_time = datetime.now()
        self._weight_used_minute = 0
        self._weight_used_5min = 0
        
        # Weight limits
        self.WEIGHT_LIMIT_MINUTE = 1200
        self.WEIGHT_LIMIT_5MIN = 6000
        
        logger.info("Binance interface initialized (public data, no auth required)")
    
    @property
    def metadata(self) -> DataSourceMetadata:
        """Return metadata describing this data source's capabilities"""
        return DataSourceMetadata(
            name="Binance",
            provider="Binance",
            description="Real-time cryptocurrency market data from the world's largest exchange",
            version="1.0.0",
            data_types=[
                DataType.PRICE,
                DataType.VOLUME,
                DataType.ORDER_BOOK,
                DataType.TRADES,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.MULTI_CURRENCY,
                Capability.MARKET_DEPTH,
                Capability.TIME_SERIES,
                Capability.WEBSOCKET_STREAMING,  # Available but not implemented yet
            ],
            response_time=ResponseTime.REAL_TIME,  # Sub-second latency
            reliability_score=0.98,  # World-class infrastructure
            cost_tier=CostTier.FREE,
            rate_limits=RateLimits(
                requests_per_minute=1200,
                requests_per_day=86400,  # 1200/min * 60 min * 24 hours
                burst_limit=6000,
            ),
            best_for=[
                "Real-time price monitoring",
                "High-frequency trading signals",
                "Order book analysis",
                "Volume analysis",
                "Cross-exchange arbitrage",
            ],
            not_recommended_for=[
                "On-chain analysis",
                "Sentiment analysis",
                "News data",
            ],
            # Public data requires no authentication
            requires_api_key=False,
        )
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data from Binance API.
        
        Args:
            request: Data request with parameters
            
        Returns:
            DataResponse with requested data
            
        Raises:
            DataNotAvailableError: If data cannot be fetched
            RateLimitError: If rate limit exceeded
        """
        start_time = datetime.now()
        
        try:
            # Extract symbol from request
            symbol = request.parameters.get("symbol", "BTC")
            binance_symbol = self.SYMBOL_MAPPING.get(symbol.upper(), self.DEFAULT_SYMBOL)
            
            # Route to appropriate handler based on data type
            if request.data_type == DataType.PRICE:
                data = await self._fetch_price(binance_symbol, request)
            elif request.data_type == DataType.ORDER_BOOK:
                data = await self._fetch_order_book(binance_symbol, request)
            elif request.data_type == DataType.TRADES:
                data = await self._fetch_recent_trades(binance_symbol, request)
            elif request.data_type == DataType.VOLUME:
                data = await self._fetch_24h_stats(binance_symbol, request)
            else:
                return DataResponse(
                    success=False,
                    source=self.metadata.name,
                    data={},
                    metadata={
                        "error": f"Data type {request.data_type} not supported by Binance interface",
                        "error_code": "UNSUPPORTED_DATA_TYPE",
                    },
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
                    "symbol": binance_symbol,
                    "exchange": "Binance",
                    "rate_limit_remaining_1m": self.WEIGHT_LIMIT_MINUTE - self._weight_used_minute,
                    "rate_limit_remaining_5m": self.WEIGHT_LIMIT_5MIN - self._weight_used_5min,
                    "data_type": request.data_type.value,
                }
            )
            
        except aiohttp.ClientError as e:
            logger.error(f"Binance API request failed: {e}")
            return DataResponse(
                success=False,
                source=self.metadata.name,
                data={},
                metadata={
                    "error": f"Failed to fetch data from Binance: {e}",
                    "error_code": "API_ERROR",
                },
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_price(self, symbol: str, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch current price for a symbol.
        
        Uses /api/v3/ticker/price endpoint (weight: 2 per symbol)
        """
        endpoint = "/api/v3/ticker/price"
        params = {"symbol": symbol}
        
        result = await self._make_request(endpoint, params, weight=2)
        
        return {
            "symbol": result["symbol"],
            "price": float(result["price"]),
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _fetch_24h_stats(self, symbol: str, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch 24-hour statistics including volume, high, low, price change.
        
        Uses /api/v3/ticker/24hr endpoint (weight: 2 per symbol)
        """
        endpoint = "/api/v3/ticker/24hr"
        params = {"symbol": symbol}
        
        result = await self._make_request(endpoint, params, weight=2)
        
        return {
            "symbol": result["symbol"],
            "price": float(result["lastPrice"]),
            "price_change": float(result["priceChange"]),
            "price_change_percent": float(result["priceChangePercent"]),
            "high_24h": float(result["highPrice"]),
            "low_24h": float(result["lowPrice"]),
            "volume_24h": float(result["volume"]),
            "quote_volume_24h": float(result["quoteVolume"]),
            "open_price": float(result["openPrice"]),
            "weighted_avg_price": float(result["weightedAvgPrice"]),
            "bid_price": float(result["bidPrice"]),
            "ask_price": float(result["askPrice"]),
            "spread": float(result["askPrice"]) - float(result["bidPrice"]),
            "spread_percent": ((float(result["askPrice"]) - float(result["bidPrice"])) / float(result["lastPrice"])) * 100,
            "trade_count": int(result["count"]),
            "timestamp": datetime.fromtimestamp(result["closeTime"] / 1000).isoformat(),
        }
    
    async def _fetch_order_book(self, symbol: str, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch order book depth.
        
        Uses /api/v3/depth endpoint (weight: varies by limit)
        - limit 5-100: weight 5
        - limit 500: weight 25
        - limit 1000: weight 50
        - limit 5000: weight 250
        """
        limit = request.parameters.get("limit", 100)
        
        # Adjust weight based on limit
        if limit <= 100:
            weight = 5
        elif limit <= 500:
            weight = 25
        elif limit <= 1000:
            weight = 50
        else:
            weight = 250
        
        endpoint = "/api/v3/depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        result = await self._make_request(endpoint, params, weight=weight)
        
        # Parse bids and asks
        bids = [[float(price), float(qty)] for price, qty in result["bids"]]
        asks = [[float(price), float(qty)] for price, qty in result["asks"]]
        
        # Calculate order book metrics
        total_bid_volume = sum(qty for _, qty in bids)
        total_ask_volume = sum(qty for _, qty in asks)
        best_bid = bids[0][0] if bids else 0
        best_ask = asks[0][0] if asks else 0
        spread = best_ask - best_bid if (best_bid and best_ask) else 0
        mid_price = (best_bid + best_ask) / 2 if (best_bid and best_ask) else 0
        
        return {
            "symbol": symbol,
            "bids": bids[:20],  # Return top 20 levels
            "asks": asks[:20],
            "bid_count": len(bids),
            "ask_count": len(asks),
            "total_bid_volume": total_bid_volume,
            "total_ask_volume": total_ask_volume,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "spread_percent": (spread / mid_price * 100) if mid_price else 0,
            "mid_price": mid_price,
            "last_update_id": result["lastUpdateId"],
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _fetch_recent_trades(self, symbol: str, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch recent trades.
        
        Uses /api/v3/trades endpoint (weight: 10)
        """
        limit = request.parameters.get("limit", 100)
        
        endpoint = "/api/v3/trades"
        params = {
            "symbol": symbol,
            "limit": min(limit, 1000)  # Max 1000
        }
        
        result = await self._make_request(endpoint, params, weight=10)
        
        # Parse trades
        trades = []
        total_volume = 0
        buy_volume = 0
        sell_volume = 0
        
        for trade in result:
            qty = float(trade["qty"])
            is_buyer_maker = trade["isBuyerMaker"]
            
            trades.append({
                "id": trade["id"],
                "price": float(trade["price"]),
                "quantity": qty,
                "time": datetime.fromtimestamp(trade["time"] / 1000).isoformat(),
                "is_buyer_maker": is_buyer_maker,
                "side": "sell" if is_buyer_maker else "buy",
            })
            
            total_volume += qty
            if is_buyer_maker:
                sell_volume += qty
            else:
                buy_volume += qty
        
        return {
            "symbol": symbol,
            "trades": trades[:50],  # Return most recent 50
            "trade_count": len(trades),
            "total_volume": total_volume,
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "buy_sell_ratio": buy_volume / sell_volume if sell_volume > 0 else 0,
            "timestamp": datetime.now().isoformat(),
        }
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        weight: int = 1
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API with rate limiting.
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            weight: Request weight for rate limiting
            
        Returns:
            JSON response data
            
        Raises:
            RateLimitError: If rate limit would be exceeded
            DataNotAvailableError: If request fails
        """
        # Check and update rate limits
        await self._check_rate_limit(weight)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add API key to headers if available (not required for public data)
        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    
                    # Update rate limit counters from headers
                    if "X-MBX-USED-WEIGHT-1M" in response.headers:
                        self._weight_used_minute = int(response.headers["X-MBX-USED-WEIGHT-1M"])
                    
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", 60)
                        raise RateLimitError(
                            f"Binance rate limit exceeded. Retry after {retry_after} seconds"
                        )
                    
                    if response.status == 418:
                        # IP banned
                        raise RateLimitError("Binance IP ban detected (418). Excessive requests.")
                    
                    if response.status >= 400:
                        error_data = await response.json()
                        error_msg = error_data.get("msg", "Unknown error")
                        raise DataNotAvailableError(
                            f"Binance API error ({response.status}): {error_msg}"
                        )
                    
                    return await response.json()
                    
        except asyncio.TimeoutError:
            raise DataNotAvailableError("Binance API request timed out")
        except aiohttp.ClientError as e:
            raise DataNotAvailableError(f"Binance API request failed: {e}")
    
    async def _check_rate_limit(self, weight: int):
        """
        Check if request would exceed rate limits.
        
        Args:
            weight: Weight of the request to check
            
        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        now = datetime.now()
        
        # Reset minute counter if needed
        if (now - self._minute_reset_time).total_seconds() >= 60:
            self._weight_used_minute = 0
            self._minute_reset_time = now
        
        # Reset 5-minute counter if needed
        if (now - self._5min_reset_time).total_seconds() >= 300:
            self._weight_used_5min = 0
            self._5min_reset_time = now
        
        # Check if request would exceed limits
        if self._weight_used_minute + weight > self.WEIGHT_LIMIT_MINUTE:
            wait_seconds = 60 - (now - self._minute_reset_time).total_seconds()
            raise RateLimitError(
                f"Binance 1-minute rate limit would be exceeded. "
                f"Wait {wait_seconds:.1f} seconds."
            )
        
        if self._weight_used_5min + weight > self.WEIGHT_LIMIT_5MIN:
            wait_seconds = 300 - (now - self._5min_reset_time).total_seconds()
            raise RateLimitError(
                f"Binance 5-minute rate limit would be exceeded. "
                f"Wait {wait_seconds:.1f} seconds."
            )
        
        # Update counters
        self._weight_used_minute += weight
        self._weight_used_5min += weight
    
    async def health_check(self) -> bool:
        """
        Check if Binance API is accessible.
        
        Returns:
            True if API is healthy
        """
        try:
            endpoint = "/api/v3/ping"
            result = await self._make_request(endpoint, weight=1)
            logger.info("Binance health check: OK")
            return True
        except Exception as e:
            logger.error(f"Binance health check failed: {e}")
            return False
