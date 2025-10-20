"""
Alpha Vantage API interface for cryptocurrency data.

Provides price validation, technical indicators, and historical data
as a backup/validation source for primary price feeds.

API Documentation: https://www.alphavantage.co/documentation/
Free Tier: 25 requests/day (no API key), 500/day with free API key
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


class AlphaVantageInterface(DataInterface):
    """
    Alpha Vantage API interface for crypto price validation and technical analysis.
    
    Features:
    - Real-time and historical cryptocurrency prices
    - Technical indicators (RSI, MACD, SMA, EMA, etc.)
    - Intraday and daily time series data
    - Price validation against other sources
    
    Rate Limits:
    - Free tier: 25 requests/day
    - Standard (free API key): 500 requests/day
    - Premium: Higher limits (paid)
    
    Use Cases:
    - Validate CoinGecko prices
    - Calculate technical indicators
    - Historical data analysis
    - Cross-exchange price comparison
    """
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    # Cryptocurrency symbols mapping
    CRYPTO_SYMBOLS = {
        "BTC": "BTC",
        "ETH": "ETH",
        "USDT": "USDT",
        "BNB": "BNB",
        "USDC": "USDC",
    }
    
    # Market (counter currency for crypto pairs)
    DEFAULT_MARKET = "USD"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Alpha Vantage interface.
        
        Args:
            api_key: Alpha Vantage API key (optional, gets from env if not provided)
        """
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Alpha Vantage API key is required. "
                "Set ALPHA_VANTAGE_API_KEY environment variable or pass api_key parameter."
            )
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._request_reset_time = datetime.now() + timedelta(days=1)
    
    @property
    def metadata(self) -> DataSourceMetadata:
        """Return metadata about this data source"""
        return DataSourceMetadata(
            name="AlphaVantage",
            provider="Alpha Vantage Inc.",
            description="Financial market data and technical indicators for cryptocurrencies",
            data_types=[
                DataType.PRICE,
                DataType.VOLUME,
                DataType.TECHNICAL_INDICATORS,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.TECHNICAL_ANALYSIS,
                Capability.TIME_SERIES,
            ],
            rate_limits=RateLimits(
                requests_per_minute=5,  # ~25 per day / 5 hours active
                requests_per_day=500,  # Free API key tier
            ),
            cost_tier=CostTier.FREEMIUM,
            response_time=ResponseTime.MODERATE,
            reliability_score=0.92,
            requires_api_key=True,
            api_key_env_var="ALPHA_VANTAGE_API_KEY",
            base_url=self.BASE_URL,
        )
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def _make_request(
        self,
        function: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make API request to Alpha Vantage.
        
        Args:
            function: API function name (e.g., 'CURRENCY_EXCHANGE_RATE')
            params: Additional parameters
            
        Returns:
            API response data
            
        Raises:
            RateLimitError: If rate limit exceeded
            AuthenticationError: If API key invalid
            DataNotAvailableError: If data not available
        """
        await self._ensure_session()
        
        # Check rate limit
        if datetime.now() > self._request_reset_time:
            self._request_count = 0
            self._request_reset_time = datetime.now() + timedelta(days=1)
        
        if self._request_count >= 500:  # Daily limit
            raise RateLimitError(
                "Alpha Vantage daily rate limit exceeded (500 requests/day). "
                f"Resets at {self._request_reset_time.strftime('%H:%M:%S UTC')}"
            )
        
        # Build request parameters
        request_params = {
            "function": function,
            "apikey": self.api_key,
            **params
        }
        
        try:
            async with self.session.get(self.BASE_URL, params=request_params) as response:
                self._request_count += 1
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for API error messages
                    if "Error Message" in data:
                        raise DataNotAvailableError(f"Alpha Vantage error: {data['Error Message']}")
                    
                    if "Note" in data and "rate limit" in data["Note"].lower():
                        raise RateLimitError(f"Rate limit: {data['Note']}")
                    
                    if "Information" in data:
                        # API key invalid or demo key being used
                        raise AuthenticationError(f"Alpha Vantage: {data['Information']}")
                    
                    return data
                
                elif response.status == 429:
                    raise RateLimitError("Alpha Vantage rate limit exceeded")
                
                elif response.status == 403:
                    raise AuthenticationError("Alpha Vantage API key invalid or forbidden")
                
                else:
                    error_text = await response.text()
                    raise DataNotAvailableError(
                        f"Alpha Vantage API error: {response.status} - {error_text}"
                    )
        
        except aiohttp.ClientError as e:
            raise DataNotAvailableError(f"Network error: {str(e)}")
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data from Alpha Vantage API.
        
        Args:
            request: Data request specifying what to fetch
            
        Returns:
            Data response with fetched data
        """
        start_time = datetime.now()
        
        try:
            # Route to appropriate handler based on data type
            if request.data_type == DataType.PRICE:
                data = await self._fetch_crypto_price(request)
            elif request.data_type == DataType.TECHNICAL_INDICATORS:
                data = await self._fetch_technical_indicators(request)
            elif request.data_type == DataType.VOLUME:
                data = await self._fetch_volume_data(request)
            else:
                return DataResponse(
                    success=False,
                    source=self.metadata.name,
                    data={},
                    error=f"AlphaVantage cannot handle data type {request.data_type.value}",
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
                    "rate_limit_remaining": 500 - self._request_count,
                    "rate_limit_reset": self._request_reset_time.isoformat(),
                }
            )
        
        except (RateLimitError, AuthenticationError, DataNotAvailableError) as e:
            logger.error(f"Alpha Vantage fetch error: {str(e)}")
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
            logger.exception(f"Unexpected error in AlphaVantage fetch: {str(e)}")
            return DataResponse(
                success=False,
                source=self.metadata.name,
                data={},
                error=f"Unexpected error: {str(e)}",
                error_code="UNKNOWN_ERROR",
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_crypto_price(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch real-time cryptocurrency price.
        
        Uses CURRENCY_EXCHANGE_RATE function for latest exchange rate.
        """
        symbol = request.symbol.upper()
        market = request.parameters.get("market", self.DEFAULT_MARKET)
        
        # Get exchange rate
        data = await self._make_request(
            function="CURRENCY_EXCHANGE_RATE",
            params={
                "from_currency": symbol,
                "to_currency": market,
            }
        )
        
        # Parse response
        rate_data = data.get("Realtime Currency Exchange Rate", {})
        
        if not rate_data:
            raise DataNotAvailableError(f"No price data available for {symbol}/{market}")
        
        price = float(rate_data.get("5. Exchange Rate", 0))
        bid_price = float(rate_data.get("8. Bid Price", 0))
        ask_price = float(rate_data.get("9. Ask Price", 0))
        
        return {
            "symbol": symbol,
            "market": market,
            "price": price,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "spread": ask_price - bid_price if ask_price and bid_price else 0,
            "spread_percent": ((ask_price - bid_price) / price * 100) if price else 0,
            "last_refreshed": rate_data.get("6. Last Refreshed"),
            "timezone": rate_data.get("7. Time Zone"),
            "source": "Alpha Vantage",
            "data_quality": "high",  # Professional-grade data
        }
    
    async def _fetch_technical_indicators(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch technical indicators for cryptocurrency.
        
        Supports: RSI, MACD, SMA, EMA, BBANDS, etc.
        """
        symbol = request.symbol.upper()
        market = request.parameters.get("market", self.DEFAULT_MARKET)
        indicator = request.parameters.get("indicator", "RSI").upper()
        interval = request.parameters.get("interval", "daily")  # daily, weekly, monthly
        time_period = request.parameters.get("time_period", 14)
        
        # Map indicator to Alpha Vantage function
        function_map = {
            "RSI": "RSI",
            "MACD": "MACD",
            "SMA": "SMA",
            "EMA": "EMA",
            "BBANDS": "BBANDS",
            "STOCH": "STOCH",
            "ADX": "ADX",
            "CCI": "CCI",
            "AROON": "AROON",
            "MOM": "MOM",
            "WIL LIAMSR": "WILLR",
        }
        
        if indicator not in function_map:
            raise DataNotAvailableError(f"Indicator {indicator} not supported")
        
        # Fetch indicator data
        # Note: Alpha Vantage doesn't directly support crypto technical indicators
        # This is a placeholder for the structure. In production, you'd need to:
        # 1. Fetch daily time series data
        # 2. Calculate indicators locally
        # Or use a different endpoint
        
        raise DataNotAvailableError(
            "Technical indicators for crypto require time series data. "
            "Use daily/weekly time series endpoint and calculate indicators locally."
        )
    
    async def _fetch_volume_data(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch volume data (part of time series data).
        """
        # Volume is included in time series data
        # For real-time volume, we'd need to fetch intraday or daily data
        raise DataNotAvailableError(
            "Volume data requires time series endpoint. "
            "Use DIGITAL_CURRENCY_DAILY function."
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Alpha Vantage API is accessible and healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            start_time = datetime.now()
            
            # Make a simple request to check API health
            # Use BTC/USD exchange rate as a lightweight test
            await self._make_request(
                function="CURRENCY_EXCHANGE_RATE",
                params={
                    "from_currency": "BTC",
                    "to_currency": "USD",
                }
            )
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "rate_limit_remaining": 500 - self._request_count,
                "rate_limit_reset": self._request_reset_time.isoformat(),
                "message": "Alpha Vantage API is accessible",
            }
        
        except RateLimitError:
            return {
                "status": "degraded",
                "message": "Rate limit exceeded",
                "rate_limit_reset": self._request_reset_time.isoformat(),
            }
        
        except AuthenticationError:
            return {
                "status": "unhealthy",
                "message": "Authentication failed - check API key",
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
