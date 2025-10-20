"""
Advanced Sentiment Analyzer

Combines multiple sentiment sources (NewsAPI, Twitter, Fear & Greed Index)
to create a unified, weighted sentiment score with trend analysis and
divergence detection.

Features:
- Multi-source sentiment aggregation
- Historical trend analysis (24h, 7d, 30d)
- Sentiment-price correlation scoring
- Divergence alerts (bullish/bearish)
- Confidence scoring based on data quality
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import logging

from .base_interface import DataRequest, DataResponse
from .metadata import DataType

logger = logging.getLogger(__name__)


@dataclass
class SentimentReading:
    """Individual sentiment reading from a source"""
    source: str
    score: float  # -1.0 to 1.0 (-1 = extreme bearish, 1 = extreme bullish)
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    raw_data: Dict[str, Any]


@dataclass
class UnifiedSentiment:
    """Unified sentiment analysis combining multiple sources"""
    composite_score: float  # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    sentiment_label: str  # "EXTREME_BULLISH", "BULLISH", "NEUTRAL", "BEARISH", "EXTREME_BEARISH"
    
    # Individual source scores
    news_score: Optional[float] = None
    social_score: Optional[float] = None
    fear_greed_score: Optional[float] = None
    
    # Trend analysis
    trend_24h: Optional[str] = None  # "IMPROVING", "STABLE", "DETERIORATING"
    trend_7d: Optional[str] = None
    
    # Divergence detection
    divergence_detected: bool = False
    divergence_type: Optional[str] = None  # "BULLISH_DIVERGENCE", "BEARISH_DIVERGENCE"
    divergence_strength: Optional[float] = None  # 0.0 to 1.0
    
    # Metadata
    sources_used: List[str] = None
    timestamp: datetime = None


class SentimentAnalyzer:
    """
    Advanced sentiment analyzer combining multiple data sources.
    
    Weights (configurable):
    - News Sentiment: 40% (professional analysis)
    - Social Sentiment: 35% (retail sentiment)
    - Fear & Greed: 25% (market psychology)
    """
    
    # Default weights for each source
    DEFAULT_WEIGHTS = {
        "news": 0.40,
        "social": 0.35,
        "fear_greed": 0.25,
    }
    
    # Sentiment thresholds
    SENTIMENT_THRESHOLDS = {
        "EXTREME_BEARISH": -0.6,
        "BEARISH": -0.2,
        "NEUTRAL": 0.2,
        "BULLISH": 0.6,
        "EXTREME_BULLISH": 1.0,
    }
    
    def __init__(
        self,
        newsapi_interface=None,
        twitter_interface=None,
        sentiment_interface=None,
        weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize sentiment analyzer.
        
        Args:
            newsapi_interface: NewsAPI interface instance
            twitter_interface: Twitter interface instance
            sentiment_interface: Fear & Greed interface instance
            weights: Custom weights for each source (must sum to 1.0)
        """
        self.newsapi = newsapi_interface
        self.twitter = twitter_interface
        self.sentiment = sentiment_interface
        
        # Use custom weights or defaults
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        # Validate weights sum to 1.0
        if abs(sum(self.weights.values()) - 1.0) > 0.01:
            logger.warning(f"Weights sum to {sum(self.weights.values())}, normalizing to 1.0")
            total = sum(self.weights.values())
            self.weights = {k: v/total for k, v in self.weights.items()}
        
        # Historical sentiment storage (in-memory for now)
        self._sentiment_history: List[UnifiedSentiment] = []
        
        logger.info(f"Sentiment analyzer initialized with weights: {self.weights}")
    
    async def analyze(
        self,
        symbol: str = "BTC",
        include_trends: bool = True,
        detect_divergence: bool = False,
        price_data: Optional[List[Dict[str, Any]]] = None
    ) -> UnifiedSentiment:
        """
        Perform unified sentiment analysis.
        
        Args:
            symbol: Cryptocurrency symbol
            include_trends: Calculate sentiment trends
            detect_divergence: Check for sentiment-price divergences
            price_data: Historical price data for divergence detection
            
        Returns:
            UnifiedSentiment object with comprehensive analysis
        """
        timestamp = datetime.now()
        readings = []
        sources_used = []
        
        # Fetch sentiment from all available sources in parallel
        tasks = []
        
        if self.newsapi:
            tasks.append(self._fetch_news_sentiment(symbol))
        if self.twitter:
            tasks.append(self._fetch_social_sentiment(symbol))
        if self.sentiment:
            tasks.append(self._fetch_fear_greed_sentiment())
        
        # Wait for all sources
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        news_score = None
        social_score = None
        fear_greed_score = None
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Sentiment fetch error: {result}")
                continue
            
            if result:
                readings.append(result)
                sources_used.append(result.source)
                
                # Track individual scores
                if result.source == "news":
                    news_score = result.score
                elif result.source == "social":
                    social_score = result.score
                elif result.source == "fear_greed":
                    fear_greed_score = result.score
        
        # Calculate weighted composite score
        if not readings:
            logger.warning("No sentiment data available from any source")
            return UnifiedSentiment(
                composite_score=0.0,
                confidence=0.0,
                sentiment_label="UNKNOWN",
                sources_used=[],
                timestamp=timestamp
            )
        
        composite_score, confidence = self._calculate_composite_score(readings)
        sentiment_label = self._classify_sentiment(composite_score)
        
        # Build unified sentiment
        unified = UnifiedSentiment(
            composite_score=composite_score,
            confidence=confidence,
            sentiment_label=sentiment_label,
            news_score=news_score,
            social_score=social_score,
            fear_greed_score=fear_greed_score,
            sources_used=sources_used,
            timestamp=timestamp
        )
        
        # Add trend analysis
        if include_trends:
            unified.trend_24h = self._calculate_trend(hours=24)
            unified.trend_7d = self._calculate_trend(days=7)
        
        # Detect divergences
        if detect_divergence and price_data:
            divergence = self._detect_divergence(price_data)
            unified.divergence_detected = divergence["detected"]
            unified.divergence_type = divergence.get("type")
            unified.divergence_strength = divergence.get("strength")
        
        # Store in history
        self._sentiment_history.append(unified)
        
        # Prune old history (keep 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        self._sentiment_history = [
            s for s in self._sentiment_history 
            if s.timestamp > cutoff
        ]
        
        return unified
    
    async def _fetch_news_sentiment(self, symbol: str) -> Optional[SentimentReading]:
        """Fetch news sentiment from NewsAPI"""
        try:
            request = DataRequest(
                data_type=DataType.NEWS,
                parameters={"symbol": symbol, "days": 1}
            )
            
            response = await self.newsapi.fetch(request)
            
            if not response.success or not response.data.get("articles"):
                return None
            
            # Calculate average sentiment from articles
            articles = response.data["articles"]
            sentiments = [a["sentiment_score"] for a in articles if "sentiment_score" in a]
            
            if not sentiments:
                return None
            
            # Convert 0-1 scale to -1 to 1 scale
            avg_sentiment = statistics.mean(sentiments)
            normalized_score = (avg_sentiment * 2) - 1  # 0->-1, 0.5->0, 1->1
            
            # Confidence based on article count and consistency
            confidence = min(len(sentiments) / 20, 1.0)  # Max confidence at 20+ articles
            stdev = statistics.stdev(sentiments) if len(sentiments) > 1 else 0.5
            confidence *= (1 - stdev)  # Lower confidence if high variance
            
            return SentimentReading(
                source="news",
                score=normalized_score,
                confidence=confidence,
                timestamp=datetime.now(),
                raw_data={"article_count": len(articles), "sentiment_stdev": stdev}
            )
            
        except Exception as e:
            logger.error(f"News sentiment fetch failed: {e}")
            return None
    
    async def _fetch_social_sentiment(self, symbol: str) -> Optional[SentimentReading]:
        """Fetch social sentiment from Twitter"""
        try:
            request = DataRequest(
                data_type=DataType.INFLUENCER_ACTIVITY,
                parameters={"symbol": symbol}
            )
            
            response = await self.twitter.fetch(request)
            
            if not response.success or not response.data.get("posts"):
                return None
            
            posts = response.data["posts"]
            sentiments = [p["sentiment"] for p in posts if "sentiment" in p]
            
            if not sentiments:
                return None
            
            # Calculate weighted average (weight by follower count)
            total_weight = sum(p.get("author_followers", 1) for p in posts)
            weighted_sum = sum(
                p["sentiment"] * p.get("author_followers", 1)
                for p in posts if "sentiment" in p
            )
            
            avg_sentiment = weighted_sum / total_weight if total_weight > 0 else 0
            normalized_score = (avg_sentiment * 2) - 1
            
            # Confidence based on post count and influencer reach
            confidence = min(len(posts) / 30, 1.0)  # Max at 30+ posts
            
            return SentimentReading(
                source="social",
                score=normalized_score,
                confidence=confidence,
                timestamp=datetime.now(),
                raw_data={"post_count": len(posts), "total_reach": total_weight}
            )
            
        except Exception as e:
            logger.error(f"Social sentiment fetch failed: {e}")
            return None
    
    async def _fetch_fear_greed_sentiment(self) -> Optional[SentimentReading]:
        """Fetch Fear & Greed Index"""
        try:
            request = DataRequest(
                data_type=DataType.SOCIAL_SENTIMENT,
                parameters={}
            )
            
            response = await self.sentiment.fetch(request)
            
            if not response.success:
                return None
            
            # Convert 0-100 scale to -1 to 1 scale
            # 0 (extreme fear) -> -1, 50 (neutral) -> 0, 100 (extreme greed) -> 1
            index_value = response.data.get("value", 50)
            normalized_score = (index_value - 50) / 50
            
            # Fear & Greed has high confidence (established index)
            confidence = 0.9
            
            return SentimentReading(
                source="fear_greed",
                score=normalized_score,
                confidence=confidence,
                timestamp=datetime.now(),
                raw_data={"index_value": index_value}
            )
            
        except Exception as e:
            logger.error(f"Fear & Greed fetch failed: {e}")
            return None
    
    def _calculate_composite_score(
        self, 
        readings: List[SentimentReading]
    ) -> Tuple[float, float]:
        """
        Calculate weighted composite score from multiple readings.
        
        Returns:
            Tuple of (composite_score, confidence)
        """
        if not readings:
            return 0.0, 0.0
        
        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0
        confidence_sum = 0.0
        
        for reading in readings:
            # Map source to weight
            source_key = reading.source.replace("fear_greed", "fear_greed")
            weight = self.weights.get(source_key, 0.0)
            
            # Apply confidence-adjusted weight
            adjusted_weight = weight * reading.confidence
            
            weighted_sum += reading.score * adjusted_weight
            total_weight += adjusted_weight
            confidence_sum += reading.confidence
        
        # Normalize
        composite_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Overall confidence is average of source confidences
        confidence = confidence_sum / len(readings) if readings else 0.0
        
        # Clamp to -1, 1 range
        composite_score = max(-1.0, min(1.0, composite_score))
        
        return composite_score, confidence
    
    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment score into label"""
        if score <= self.SENTIMENT_THRESHOLDS["EXTREME_BEARISH"]:
            return "EXTREME_BEARISH"
        elif score <= self.SENTIMENT_THRESHOLDS["BEARISH"]:
            return "BEARISH"
        elif score <= self.SENTIMENT_THRESHOLDS["NEUTRAL"]:
            return "NEUTRAL"
        elif score <= self.SENTIMENT_THRESHOLDS["BULLISH"]:
            return "BULLISH"
        else:
            return "EXTREME_BULLISH"
    
    def _calculate_trend(self, hours: int = 0, days: int = 0) -> str:
        """Calculate sentiment trend over time period"""
        if not self._sentiment_history:
            return "INSUFFICIENT_DATA"
        
        # Calculate lookback period
        lookback = timedelta(hours=hours, days=days)
        cutoff = datetime.now() - lookback
        
        # Get historical sentiments
        historical = [
            s for s in self._sentiment_history
            if s.timestamp > cutoff
        ]
        
        if len(historical) < 2:
            return "INSUFFICIENT_DATA"
        
        # Compare first half vs second half
        mid = len(historical) // 2
        first_half_avg = statistics.mean(s.composite_score for s in historical[:mid])
        second_half_avg = statistics.mean(s.composite_score for s in historical[mid:])
        
        change = second_half_avg - first_half_avg
        
        # Classify trend
        if change > 0.1:
            return "IMPROVING"
        elif change < -0.1:
            return "DETERIORATING"
        else:
            return "STABLE"
    
    def _detect_divergence(
        self,
        price_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Detect sentiment-price divergences.
        
        Bullish divergence: Price making lower lows, sentiment improving
        Bearish divergence: Price making higher highs, sentiment deteriorating
        """
        if len(self._sentiment_history) < 10 or len(price_data) < 10:
            return {"detected": False}
        
        # Get recent data (last 10 points)
        recent_sentiment = self._sentiment_history[-10:]
        recent_prices = price_data[-10:]
        
        # Calculate trends
        sentiment_trend = statistics.linear_regression(
            range(len(recent_sentiment)),
            [s.composite_score for s in recent_sentiment]
        )
        
        price_trend = statistics.linear_regression(
            range(len(recent_prices)),
            [p["price"] for p in recent_prices]
        )
        
        # Detect divergences
        sentiment_slope = sentiment_trend[0]  # Slope
        price_slope = price_trend[0]
        
        # Bullish divergence: price down, sentiment up
        if price_slope < -0.01 and sentiment_slope > 0.01:
            strength = min(abs(sentiment_slope / price_slope), 1.0)
            return {
                "detected": True,
                "type": "BULLISH_DIVERGENCE",
                "strength": strength
            }
        
        # Bearish divergence: price up, sentiment down
        if price_slope > 0.01 and sentiment_slope < -0.01:
            strength = min(abs(sentiment_slope / price_slope), 1.0)
            return {
                "detected": True,
                "type": "BEARISH_DIVERGENCE",
                "strength": strength
            }
        
        return {"detected": False}
    
    def get_sentiment_summary(self) -> Dict[str, Any]:
        """Get summary statistics of sentiment history"""
        if not self._sentiment_history:
            return {"error": "No historical data"}
        
        recent = self._sentiment_history[-24:]  # Last 24 readings
        
        return {
            "current": recent[-1].composite_score if recent else 0,
            "avg_24h": statistics.mean(s.composite_score for s in recent),
            "max_24h": max(s.composite_score for s in recent),
            "min_24h": min(s.composite_score for s in recent),
            "volatility": statistics.stdev(s.composite_score for s in recent) if len(recent) > 1 else 0,
            "readings_count": len(recent),
            "sources_active": len(set(src for s in recent for src in s.sources_used)),
        }
