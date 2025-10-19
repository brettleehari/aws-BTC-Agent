"""
CoinGecko data interface implementation.

Provides cryptocurrency price and market data from CoinGecko API.
Free tier available with rate limiting.
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    RateLimitError,
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


class CoinGeckoInterface(DataInterface):
    """
    CoinGecko API interface for cryptocurrency market data.
    
    Supports:
    - Real-time price data
    - Market cap and volume
    - Historical price data
    - Multi-currency support
    """
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.api_key = api_key or os.getenv('COINGECKO_API_KEY')
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="CoinGecko",
            provider="CoinGecko",
            description="Cryptocurrency price and market data API with comprehensive coverage",
            version="3.0.0",
            data_types=[
                DataType.PRICE,
                DataType.MARKET_CAP,
                DataType.VOLUME,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.MULTI_CURRENCY,
                Capability.MULTI_EXCHANGE,
                Capability.TIME_SERIES,
                Capability.RATE_LIMITED,
            ],
            response_time=ResponseTime.FAST,
            reliability_score=0.95,
            cost_tier=CostTier.FREEMIUM,
            rate_limits=RateLimits(
                requests_per_minute=50,
                requests_per_hour=None,
                requests_per_day=10000 if self.api_key else 100,
            ),
            best_for=[
                "price_queries",
                "market_overview",
                "quick_checks",
                "multi_currency_data",
                "historical_price",
            ],
            not_recommended_for=[
                "on_chain_analysis",
                "whale_tracking",
                "derivatives_data",
            ],
            base_url=self.BASE_URL,
            requires_api_key=False,
            api_key_env_var="COINGECKO_API_KEY",
            documentation_url="https://www.coingecko.com/en/api/documentation",
            data_freshness="real-time",
            historical_data_available=True,
            historical_data_range="2013-present",
            example_queries=[
                {
                    "description": "Get BTC price in USD",
                    "request": {
                        "data_type": "price",
                        "symbol": "BTC",
                        "parameters": {"vs_currency": "usd"}
                    }
                },
                {
                    "description": "Get 7-day price history",
                    "request": {
                        "data_type": "price",
                        "symbol": "BTC",
                        "timeframe": "7d",
                        "parameters": {"vs_currency": "usd"}
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
        Fetch data from CoinGecko API.
        
        Args:
            request: Data request
            
        Returns:
            Data response with market data
        """
        start_time = datetime.now()
        
        try:
            await self.validate_request(request)
            await self._ensure_session()
            
            # Route to appropriate method based on data type
            if request.data_type == DataType.PRICE:
                data = await self._fetch_price(request)
            elif request.data_type == DataType.MARKET_CAP:
                data = await self._fetch_market_cap(request)
            elif request.data_type == DataType.VOLUME:
                data = await self._fetch_volume(request)
            else:
                raise DataNotAvailableError(
                    f"CoinGecko does not support data type: {request.data_type.value}"
                )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            self._call_count += 1
            
            return DataResponse(
                success=True,
                source="CoinGecko",
                data=data,
                metadata={
                    'data_type': request.data_type.value,
                    'symbol': request.symbol,
                    'api_version': 'v3',
                },
                request_time=start_time,
                response_time=end_time,
                data_timestamp=datetime.now(),
                latency_ms=latency,
            )
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"CoinGecko fetch error: {e}")
            
            return DataResponse(
                success=False,
                source="CoinGecko",
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_price(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch current price data"""
        coin_id = self._symbol_to_coin_id(request.symbol)
        vs_currency = request.parameters.get('vs_currency', 'usd')
        
        url = f"{self.BASE_URL}/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': vs_currency,
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true',
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 429:
                raise RateLimitError("CoinGecko rate limit exceeded")
            
            response.raise_for_status()
            data = await response.json()
            
            if coin_id not in data:
                raise DataNotAvailableError(f"No data for {request.symbol}")
            
            coin_data = data[coin_id]
            
            return {
                'symbol': request.symbol,
                'price': coin_data.get(vs_currency),
                'currency': vs_currency,
                'market_cap': coin_data.get(f'{vs_currency}_market_cap'),
                'volume_24h': coin_data.get(f'{vs_currency}_24h_vol'),
                'price_change_24h_percent': coin_data.get(f'{vs_currency}_24h_change'),
            }
    
    async def _fetch_market_cap(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch market cap data"""
        price_data = await self._fetch_price(request)
        return {
            'symbol': request.symbol,
            'market_cap': price_data['market_cap'],
            'currency': price_data['currency'],
        }
    
    async def _fetch_volume(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch volume data"""
        price_data = await self._fetch_price(request)
        return {
            'symbol': request.symbol,
            'volume_24h': price_data['volume_24h'],
            'currency': price_data['currency'],
        }
    
    def _symbol_to_coin_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko coin ID"""
        # Common mappings
        mapping = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'ADA': 'cardano',
        }
        return mapping.get(symbol.upper(), symbol.lower())
    
    async def health_check(self) -> bool:
        """Check if CoinGecko API is available"""
        try:
            await self._ensure_session()
            url = f"{self.BASE_URL}/ping"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"CoinGecko health check failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup session on deletion"""
        if self.session:
            try:
                asyncio.create_task(self._close_session())
            except RuntimeError:
                pass  # Event loop may be closed
