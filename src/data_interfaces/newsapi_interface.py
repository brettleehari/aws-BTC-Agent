"""
NewsAPI interface for cryptocurrency news and sentiment analysis.

Fetches breaking news about Bitcoin and cryptocurrencies from major
news sources and performs sentiment analysis on articles.
"""

import os
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from .base_interface import (
    DataInterface,
    DataRequest,
    DataResponse,
    RateLimitError,
    DataNotAvailableError,
    AuthenticationError,
)
from .metadata import (
    DataSourceMetadata,
    DataType,
    Capability,
    ResponseTime,
    CostTier,
    RateLimits,
)

logger = logging.getLogger(__name__)


class NewsAPIInterface(DataInterface):
    """
    NewsAPI.org integration for cryptocurrency news.
    
    Fetches breaking news articles from major publications about
    Bitcoin and cryptocurrencies, with sentiment analysis.
    
    Free tier: 100 requests/day
    Paid tier: Unlimited requests
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    # News sources that cover crypto
    CRYPTO_SOURCES = [
        "bloomberg", "reuters", "financial-times", "the-wall-street-journal",
        "cnbc", "cnn", "bbc-news", "business-insider", "techcrunch",
        "the-verge", "wired", "fortune", "coindesk"
    ]
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        
        # Load API key from environment or parameter
        self.api_key = api_key or os.getenv('NEWSAPI_KEY')
        
        if not self.api_key:
            raise ValueError(
                "NewsAPI key is required. "
                "Set NEWSAPI_KEY environment variable or pass api_key parameter."
            )
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="NewsAPI",
            provider="NewsAPI.org",
            description="Breaking cryptocurrency news and sentiment analysis from major publications",
            version="2.0.0",
            data_types=[
                DataType.NEWS,
                DataType.SOCIAL_SENTIMENT,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.SENTIMENT_ANALYSIS,
                Capability.HISTORICAL,
            ],
            response_time=ResponseTime.MODERATE,
            reliability_score=0.90,
            cost_tier=CostTier.FREEMIUM,
            rate_limits=RateLimits(
                requests_per_minute=None,
                requests_per_hour=None,
                requests_per_day=100,  # Free tier limit
            ),
            best_for=[
                "breaking_news",
                "news_sentiment",
                "regulatory_updates",
                "mainstream_coverage",
                "institutional_news",
            ],
            not_recommended_for=[
                "price_data",
                "on_chain_metrics",
                "technical_indicators",
            ],
            base_url=self.BASE_URL,
            requires_api_key=True,
            api_key_env_var="NEWSAPI_KEY",
            documentation_url="https://newsapi.org/docs",
            data_freshness="real-time (15-minute delay on free tier)",
            historical_data_available=True,
            historical_data_range="30 days (free tier), unlimited (paid)",
        )
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch cryptocurrency news from NewsAPI.
        
        Args:
            request: Data request with parameters:
                - timeframe: "24h", "7d", etc. (default: "24h")
                - parameters:
                    - sources: List of news sources to query
                    - language: "en" (default)
                    - sort_by: "relevancy", "popularity", "publishedAt"
                    - page_size: Number of articles (default: 20)
        
        Returns:
            DataResponse with news articles and sentiment analysis
        """
        start_time = datetime.now()
        
        try:
            await self.validate_request(request)
            await self._ensure_session()
            
            # Route based on data type
            if request.data_type == DataType.NEWS:
                data = await self._fetch_news_articles(request)
            elif request.data_type == DataType.SOCIAL_SENTIMENT:
                data = await self._fetch_news_sentiment(request)
            else:
                raise DataNotAvailableError(
                    f"NewsAPI does not support data type: {request.data_type.value}"
                )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            self._call_count += 1
            
            return DataResponse(
                success=True,
                source="NewsAPI",
                data=data,
                metadata={
                    'data_type': request.data_type.value,
                    'api_version': 'v2',
                },
                request_time=start_time,
                response_time=end_time,
                data_timestamp=datetime.now(),
                latency_ms=latency,
            )
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"NewsAPI fetch error: {e}")
            
            return DataResponse(
                success=False,
                source="NewsAPI",
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_news_articles(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch news articles about Bitcoin/crypto"""
        
        # Parse timeframe
        timeframe = request.timeframe or "24h"
        hours = self._parse_timeframe(timeframe)
        from_date = datetime.now() - timedelta(hours=hours)
        
        # Build query parameters
        params = {
            'apiKey': self.api_key,
            'q': self._build_query(request.symbol),
            'language': request.parameters.get('language', 'en'),
            'sortBy': request.parameters.get('sort_by', 'publishedAt'),
            'pageSize': request.parameters.get('page_size', 20),
            'from': from_date.isoformat(),
        }
        
        # Add sources if specified
        sources = request.parameters.get('sources', self.CRYPTO_SOURCES[:5])
        if sources:
            params['sources'] = ','.join(sources)
        
        # Make API request
        url = f"{self.BASE_URL}/everything"
        
        async with self.session.get(url, params=params) as response:
            if response.status == 401:
                raise AuthenticationError("Invalid NewsAPI key")
            elif response.status == 429:
                raise RateLimitError("NewsAPI rate limit exceeded (100 requests/day on free tier)")
            elif response.status != 200:
                error_text = await response.text()
                raise DataNotAvailableError(f"NewsAPI error: {error_text}")
            
            data = await response.json()
        
        # Parse articles
        articles = data.get('articles', [])
        
        # Analyze sentiment for each article
        analyzed_articles = []
        for article in articles:
            sentiment = self._analyze_article_sentiment(article)
            analyzed_articles.append({
                'title': article.get('title'),
                'description': article.get('description'),
                'content': article.get('content'),
                'url': article.get('url'),
                'source': article.get('source', {}).get('name'),
                'author': article.get('author'),
                'published_at': article.get('publishedAt'),
                'sentiment': sentiment,
                'sentiment_score': sentiment['score'],
            })
        
        # Calculate overall sentiment
        overall_sentiment = self._calculate_overall_sentiment(analyzed_articles)
        
        return {
            'symbol': request.symbol,
            'metric': 'news_articles',
            'articles': analyzed_articles,
            'total_articles': len(analyzed_articles),
            'timeframe': timeframe,
            'overall_sentiment': overall_sentiment,
            'timestamp': datetime.now().isoformat(),
        }
    
    async def _fetch_news_sentiment(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch aggregated news sentiment"""
        
        # Fetch articles first
        articles_data = await self._fetch_news_articles(request)
        
        # Extract sentiment analysis
        sentiment = articles_data['overall_sentiment']
        
        return {
            'symbol': request.symbol,
            'metric': 'news_sentiment',
            'sentiment_score': sentiment['score'],
            'classification': sentiment['classification'],
            'signal': sentiment['signal'],
            'confidence': sentiment['confidence'],
            'articles_analyzed': articles_data['total_articles'],
            'positive_count': sentiment['positive_count'],
            'negative_count': sentiment['negative_count'],
            'neutral_count': sentiment['neutral_count'],
            'top_headlines': [
                {
                    'title': a['title'],
                    'source': a['source'],
                    'sentiment_score': a['sentiment_score']
                }
                for a in articles_data['articles'][:5]
            ],
            'timestamp': datetime.now().isoformat(),
        }
    
    def _build_query(self, symbol: str) -> str:
        """Build search query for news articles"""
        queries = {
            'BTC': 'Bitcoin OR BTC OR cryptocurrency',
            'ETH': 'Ethereum OR ETH OR crypto',
            'crypto': 'cryptocurrency OR Bitcoin OR crypto market',
        }
        return queries.get(symbol, f'{symbol} cryptocurrency')
    
    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        if timeframe.endswith('h'):
            return int(timeframe[:-1])
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 24
        elif timeframe.endswith('w'):
            return int(timeframe[:-1]) * 24 * 7
        else:
            return 24  # Default to 24 hours
    
    def _analyze_article_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment of a news article.
        
        Uses keyword-based analysis. For production, consider using
        an LLM like Claude 3 Haiku for more accurate sentiment analysis.
        """
        text = f"{article.get('title', '')} {article.get('description', '')}"
        text = text.lower()
        
        # Bullish keywords
        bullish_keywords = [
            'bullish', 'surge', 'rally', 'soar', 'climb', 'gain', 'rise',
            'breakthrough', 'adoption', 'institutional', 'mainstream',
            'positive', 'optimistic', 'growth', 'boom', 'uptick', 'advance',
            'outperform', 'investment', 'approve', 'approval', 'support'
        ]
        
        # Bearish keywords
        bearish_keywords = [
            'bearish', 'crash', 'plunge', 'drop', 'fall', 'decline', 'sink',
            'concern', 'risk', 'warning', 'fear', 'uncertain', 'volatile',
            'negative', 'pessimistic', 'downturn', 'loss', 'ban', 'regulate',
            'crackdown', 'fraud', 'scam', 'hack', 'vulnerable'
        ]
        
        # Count keyword matches
        bullish_count = sum(1 for kw in bullish_keywords if kw in text)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text)
        
        # Calculate sentiment score (0-1, where 0.5 is neutral)
        total_keywords = bullish_count + bearish_count
        if total_keywords == 0:
            score = 0.5  # Neutral
            classification = "Neutral"
        else:
            score = bullish_count / total_keywords
            if score >= 0.7:
                classification = "Very Bullish"
            elif score >= 0.6:
                classification = "Bullish"
            elif score >= 0.4:
                classification = "Neutral"
            elif score >= 0.3:
                classification = "Bearish"
            else:
                classification = "Very Bearish"
        
        return {
            'score': score,
            'classification': classification,
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
        }
    
    def _calculate_overall_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall sentiment from multiple articles"""
        
        if not articles:
            return {
                'score': 0.5,
                'classification': 'Neutral',
                'signal': 'No Data',
                'confidence': 0.0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
            }
        
        # Calculate weighted average (recent articles weighted higher)
        scores = [a['sentiment_score'] for a in articles]
        avg_score = sum(scores) / len(scores)
        
        # Classify overall sentiment
        if avg_score >= 0.65:
            classification = "Bullish"
            signal = "Positive News Flow"
        elif avg_score >= 0.55:
            classification = "Slightly Bullish"
            signal = "Cautiously Optimistic"
        elif avg_score >= 0.45:
            classification = "Neutral"
            signal = "Mixed Signals"
        elif avg_score >= 0.35:
            classification = "Slightly Bearish"
            signal = "Cautiously Pessimistic"
        else:
            classification = "Bearish"
            signal = "Negative News Flow"
        
        # Count sentiment distribution
        positive_count = sum(1 for s in scores if s >= 0.6)
        negative_count = sum(1 for s in scores if s <= 0.4)
        neutral_count = len(scores) - positive_count - negative_count
        
        # Calculate confidence based on agreement
        dominant_count = max(positive_count, negative_count, neutral_count)
        confidence = dominant_count / len(scores)
        
        return {
            'score': avg_score,
            'classification': classification,
            'signal': signal,
            'confidence': confidence,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'interpretation': self._interpret_sentiment(avg_score, confidence),
        }
    
    def _interpret_sentiment(self, score: float, confidence: float) -> str:
        """Generate human-readable interpretation"""
        if confidence >= 0.7:
            strength = "Strong"
        elif confidence >= 0.5:
            strength = "Moderate"
        else:
            strength = "Weak"
        
        if score >= 0.65:
            return f"{strength} positive news coverage. Market sentiment favors bullish outlook."
        elif score >= 0.55:
            return f"{strength} slightly positive news. Cautiously optimistic market tone."
        elif score >= 0.45:
            return f"{strength} mixed news coverage. No clear directional signal."
        elif score >= 0.35:
            return f"{strength} slightly negative news. Market showing concern."
        else:
            return f"{strength} negative news coverage. Bearish sentiment in media."
    
    async def health_check(self) -> bool:
        """Check if NewsAPI is accessible"""
        try:
            await self._ensure_session()
            
            # Simple test query
            url = f"{self.BASE_URL}/top-headlines"
            params = {
                'apiKey': self.api_key,
                'category': 'business',
                'pageSize': 1,
            }
            
            async with self.session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"NewsAPI health check failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session') and self.session:
            try:
                import asyncio
                asyncio.create_task(self._close_session())
            except RuntimeError:
                pass  # Event loop may be closed
