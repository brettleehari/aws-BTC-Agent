"""
Sentiment data interface implementation.

Aggregates sentiment data from multiple sources including:
- Alternative.me Fear & Greed Index
- Social media sentiment (Twitter/X)
- News sentiment
"""

import os
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
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


class SentimentInterface(DataInterface):
    """
    Sentiment analysis interface aggregating multiple sources.
    
    Supports:
    - Fear & Greed Index from Alternative.me
    - Social media sentiment analysis
    - News sentiment aggregation
    - Sentiment trends and historical data
    """
    
    FEAR_GREED_URL = "https://api.alternative.me/fng/"
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="SentimentAnalyzer",
            provider="Multiple Sources",
            description="Aggregated cryptocurrency sentiment analysis from Fear & Greed Index, social media, and news",
            version="1.0.0",
            data_types=[
                DataType.SOCIAL_SENTIMENT,
                DataType.NEWS,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.SENTIMENT_ANALYSIS,
                Capability.AGGREGATION,
                Capability.TIME_SERIES,
            ],
            response_time=ResponseTime.FAST,
            reliability_score=0.90,
            cost_tier=CostTier.FREE,
            rate_limits=RateLimits(
                requests_per_minute=30,
                requests_per_hour=None,
                requests_per_day=None,
            ),
            best_for=[
                "sentiment_analysis",
                "market_mood",
                "fear_greed_tracking",
                "social_trends",
                "quick_sentiment_checks",
            ],
            not_recommended_for=[
                "price_data",
                "on_chain_analysis",
                "technical_indicators",
            ],
            base_url=self.FEAR_GREED_URL,
            requires_api_key=False,
            api_key_env_var=None,
            documentation_url="https://alternative.me/crypto/fear-and-greed-index/",
            data_freshness="daily updates",
            historical_data_available=True,
            historical_data_range="2018-present",
            example_queries=[
                {
                    "description": "Get current Fear & Greed Index",
                    "request": {
                        "data_type": "social_sentiment",
                        "symbol": "BTC",
                        "parameters": {"metric": "fear_greed"}
                    }
                },
                {
                    "description": "Get 30-day sentiment history",
                    "request": {
                        "data_type": "social_sentiment",
                        "symbol": "BTC",
                        "timeframe": "30d",
                        "parameters": {"metric": "fear_greed"}
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
        Fetch sentiment data.
        
        Args:
            request: Data request
            
        Returns:
            Data response with sentiment analysis
        """
        start_time = datetime.now()
        
        try:
            await self.validate_request(request)
            await self._ensure_session()
            
            # Route to appropriate method based on data type
            if request.data_type == DataType.SOCIAL_SENTIMENT:
                data = await self._fetch_social_sentiment(request)
            elif request.data_type == DataType.NEWS:
                data = await self._fetch_news_sentiment(request)
            else:
                raise DataNotAvailableError(
                    f"SentimentAnalyzer does not support data type: {request.data_type.value}"
                )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            self._call_count += 1
            
            return DataResponse(
                success=True,
                source="SentimentAnalyzer",
                data=data,
                metadata={
                    'data_type': request.data_type.value,
                    'symbol': request.symbol,
                    'sources': ['alternative.me', 'aggregated'],
                },
                request_time=start_time,
                response_time=end_time,
                data_timestamp=datetime.now(),
                latency_ms=latency,
            )
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"SentimentAnalyzer fetch error: {e}")
            
            return DataResponse(
                success=False,
                source="SentimentAnalyzer",
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_social_sentiment(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch social sentiment including Fear & Greed Index"""
        metric = request.parameters.get('metric', 'fear_greed')
        
        if metric == 'fear_greed':
            return await self._fetch_fear_greed(request)
        else:
            # Default to fear & greed if unknown metric
            return await self._fetch_fear_greed(request)
    
    async def _fetch_fear_greed(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch Fear & Greed Index from Alternative.me"""
        
        # Determine how many days of data to fetch
        limit = 1  # Default to current
        if request.timeframe:
            if request.timeframe.endswith('d'):
                limit = int(request.timeframe[:-1])
            elif request.timeframe.endswith('w'):
                limit = int(request.timeframe[:-1]) * 7
            elif request.timeframe.endswith('m'):
                limit = int(request.timeframe[:-1]) * 30
        
        params = {'limit': min(limit, 365)}  # API max is likely around 365
        
        async with self.session.get(self.FEAR_GREED_URL, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            
            if 'data' not in data:
                raise DataNotAvailableError("No Fear & Greed data available")
            
            fng_data = data['data']
            
            # Process the data
            processed = []
            for entry in fng_data:
                processed.append({
                    'value': int(entry['value']),
                    'value_classification': entry['value_classification'],
                    'timestamp': datetime.fromtimestamp(int(entry['timestamp'])).isoformat(),
                    'time_until_update': entry.get('time_until_update'),
                })
            
            # Calculate statistics
            values = [int(entry['value']) for entry in fng_data]
            current = processed[0] if processed else None
            
            return {
                'symbol': request.symbol,
                'metric': 'fear_greed_index',
                'current': current,
                'history': processed,
                'statistics': {
                    'average': sum(values) / len(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'trend': self._calculate_trend(values),
                },
                'interpretation': self._interpret_fear_greed(current['value'] if current else 0),
            }
    
    async def _fetch_news_sentiment(self, request: DataRequest) -> Dict[str, Any]:
        """
        Fetch news sentiment.
        
        Note: This is a placeholder for future news sentiment integration.
        Could integrate with CryptoPanic, NewsAPI, or similar services.
        """
        return {
            'symbol': request.symbol,
            'metric': 'news_sentiment',
            'status': 'coming_soon',
            'message': 'News sentiment analysis will be available in future updates',
            'sources': ['cryptopanic', 'newsapi', 'reddit'],
        }
    
    def _calculate_trend(self, values: List[int]) -> str:
        """Calculate sentiment trend from historical values"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Compare recent vs older values
        recent = sum(values[:len(values)//3]) / (len(values)//3)
        older = sum(values[len(values)//3:]) / (len(values) - len(values)//3)
        
        diff = recent - older
        
        if diff > 10:
            return "increasing"
        elif diff < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _interpret_fear_greed(self, value: int) -> Dict[str, Any]:
        """Interpret Fear & Greed Index value"""
        if value <= 25:
            classification = "Extreme Fear"
            signal = "Strong Buy Signal"
            description = "The market is in extreme fear. This is often a good buying opportunity."
        elif value <= 45:
            classification = "Fear"
            signal = "Buy Signal"
            description = "The market is fearful. Consider accumulating positions."
        elif value <= 55:
            classification = "Neutral"
            signal = "Hold"
            description = "The market sentiment is neutral. No clear signal."
        elif value <= 75:
            classification = "Greed"
            signal = "Caution"
            description = "The market is greedy. Consider taking profits."
        else:
            classification = "Extreme Greed"
            signal = "Strong Sell Signal"
            description = "The market is in extreme greed. High risk of correction."
        
        return {
            'value': value,
            'classification': classification,
            'signal': signal,
            'description': description,
            'risk_level': 'high' if value > 75 or value < 25 else 'medium' if value > 55 or value < 45 else 'low',
        }
    
    async def health_check(self) -> bool:
        """Check if sentiment sources are available"""
        try:
            await self._ensure_session()
            
            # Check Fear & Greed API
            async with self.session.get(
                self.FEAR_GREED_URL,
                params={'limit': 1},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"SentimentAnalyzer health check failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup session on deletion"""
        if self.session:
            try:
                asyncio.create_task(self._close_session())
            except RuntimeError:
                pass  # Event loop may be closed
