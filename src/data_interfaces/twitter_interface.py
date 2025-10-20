"""
Twitter data interface implementation for Bitcoin influencer monitoring.

Tracks top Bitcoin influencers and generates signals from their posts.
Uses Twitter API v2 with proper rate limiting and credential management.
"""

import os
import json
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from pathlib import Path

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


class TwitterInterface(DataInterface):
    """
    Twitter API v2 interface for Bitcoin influencer monitoring.
    
    Tracks tweets from key Bitcoin influencers and generates
    market intelligence signals based on their posts.
    """
    
    BASE_URL = "https://api.twitter.com/2"
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        
        # Load credentials from environment
        self.api_key = api_key or os.getenv('TWITTER_API_KEY')
        self.api_secret = os.getenv('TWITTER_API_SECRET')
        self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        
        if not self.bearer_token:
            raise ValueError(
                "Twitter Bearer Token is required. "
                "Set TWITTER_BEARER_TOKEN environment variable."
            )
        
        # Load influencer configuration
        self.influencers = self._load_influencer_config()
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_remaining = 900
        self._rate_limit_reset = datetime.now()
    
    def _load_influencer_config(self) -> Dict[str, Any]:
        """Load Twitter influencer configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "twitter_intelligence.json"
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                return data['twitter_intelligence_config']
        except Exception as e:
            logger.warning(f"Could not load Twitter config: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file not found"""
        return {
            "top_bitcoin_twitter_accounts": [
                {
                    "handle": "@saylor",
                    "name": "Michael Saylor",
                    "priority": 1,
                    "weight": 0.95,
                    "check_frequency": "real_time"
                }
            ]
        }
    
    @property
    def metadata(self) -> DataSourceMetadata:
        return DataSourceMetadata(
            name="TwitterIntelligence",
            provider="Twitter API v2",
            description="Bitcoin influencer monitoring and sentiment analysis from top crypto Twitter accounts",
            version="2.0.0",
            data_types=[
                DataType.SOCIAL_SENTIMENT,
                DataType.NEWS,
                DataType.INFLUENCER_ACTIVITY,
            ],
            capabilities=[
                Capability.REAL_TIME,
                Capability.HISTORICAL,
                Capability.SENTIMENT_ANALYSIS,
                Capability.INFLUENCER_TRACKING,
                Capability.RATE_LIMITED,
            ],
            response_time=ResponseTime.FAST,
            reliability_score=0.92,
            cost_tier=CostTier.FREEMIUM,
            rate_limits=RateLimits(
                requests_per_minute=15,
                requests_per_hour=900,
                requests_per_day=None,
            ),
            best_for=[
                "influencer_signals",
                "social_sentiment",
                "whale_alerts",
                "narrative_tracking",
                "institutional_signals",
            ],
            not_recommended_for=[
                "price_data",
                "on_chain_metrics",
                "technical_indicators",
            ],
            base_url=self.BASE_URL,
            requires_api_key=True,
            api_key_env_var="TWITTER_BEARER_TOKEN",
            documentation_url="https://developer.twitter.com/en/docs/twitter-api",
            data_freshness="real-time (5-60 second delay)",
            historical_data_available=True,
            historical_data_range="7 days (free tier)",
        )
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created with auth headers"""
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
            }
            self.session = aiohttp.ClientSession(headers=headers)
    
    async def _close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _check_rate_limit(self):
        """Check if we're within rate limits"""
        if self._rate_limit_remaining <= 1:
            wait_time = (self._rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.0f}s")
                raise RateLimitError(f"Twitter rate limit exceeded. Reset at {self._rate_limit_reset}")
    
    async def fetch(self, request: DataRequest) -> DataResponse:
        """
        Fetch data from Twitter API.
        
        Args:
            request: Data request
            
        Returns:
            Data response with Twitter intelligence
        """
        start_time = datetime.now()
        
        try:
            await self.validate_request(request)
            await self._ensure_session()
            await self._check_rate_limit()
            
            # Route to appropriate method based on data type
            if request.data_type == DataType.SOCIAL_SENTIMENT:
                data = await self._fetch_influencer_sentiment(request)
            elif request.data_type == DataType.NEWS:
                data = await self._fetch_influencer_news(request)
            elif request.data_type == DataType.INFLUENCER_ACTIVITY:
                data = await self._fetch_specific_influencer(request)
            else:
                raise DataNotAvailableError(
                    f"TwitterIntelligence does not support data type: {request.data_type.value}"
                )
            
            end_time = datetime.now()
            latency = (end_time - start_time).total_seconds() * 1000
            
            self._call_count += 1
            
            return DataResponse(
                success=True,
                source="TwitterIntelligence",
                data=data,
                metadata={
                    'data_type': request.data_type.value,
                    'api_version': 'v2',
                    'rate_limit_remaining': self._rate_limit_remaining,
                },
                request_time=start_time,
                response_time=end_time,
                data_timestamp=datetime.now(),
                latency_ms=latency,
            )
            
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"TwitterIntelligence fetch error: {e}")
            
            return DataResponse(
                success=False,
                source="TwitterIntelligence",
                data={},
                error=str(e),
                error_code=type(e).__name__,
                request_time=start_time,
                response_time=datetime.now(),
            )
    
    async def _fetch_influencer_sentiment(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch aggregated sentiment from all influencers"""
        
        # Get high-priority accounts
        accounts = self.influencers.get('top_bitcoin_twitter_accounts', [])
        high_priority = [acc for acc in accounts if acc['priority'] <= 5]
        
        # Fetch recent tweets from each
        all_tweets = []
        sentiment_scores = []
        
        for account in high_priority[:3]:  # Limit to top 3 to avoid rate limits
            try:
                tweets = await self._fetch_user_tweets(account['handle'])
                all_tweets.extend(tweets)
                
                # Calculate sentiment for this account
                account_sentiment = self._analyze_sentiment(tweets)
                sentiment_scores.append({
                    'account': account['handle'],
                    'sentiment': account_sentiment,
                    'weight': account.get('weight', 0.5),
                    'tweet_count': len(tweets)
                })
            except Exception as e:
                logger.warning(f"Error fetching {account['handle']}: {e}")
        
        # Aggregate weighted sentiment
        total_weight = sum(s['weight'] for s in sentiment_scores)
        weighted_sentiment = sum(
            s['sentiment'] * s['weight'] for s in sentiment_scores
        ) / total_weight if total_weight > 0 else 0.5
        
        return {
            'symbol': request.symbol,
            'metric': 'influencer_sentiment',
            'sentiment_score': weighted_sentiment,
            'classification': self._classify_sentiment(weighted_sentiment),
            'accounts_analyzed': len(sentiment_scores),
            'total_tweets': len(all_tweets),
            'individual_scores': sentiment_scores,
            'timestamp': datetime.now().isoformat(),
            'interpretation': self._interpret_sentiment(weighted_sentiment),
        }
    
    async def _fetch_influencer_news(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch latest news/announcements from influencers"""
        
        # Get accounts known for breaking news
        accounts = self.influencers.get('top_bitcoin_twitter_accounts', [])
        news_accounts = [
            acc for acc in accounts 
            if 'whale' in acc.get('tags', []) or 'government' in acc.get('tags', [])
        ][:3]
        
        latest_news = []
        
        for account in news_accounts:
            try:
                tweets = await self._fetch_user_tweets(account['handle'], max_results=5)
                for tweet in tweets:
                    # Check if tweet contains news-worthy keywords
                    if self._is_newsworthy(tweet):
                        latest_news.append({
                            'account': account['handle'],
                            'account_name': account['name'],
                            'text': tweet['text'],
                            'created_at': tweet['created_at'],
                            'engagement': tweet.get('public_metrics', {}),
                            'url': f"https://twitter.com/{account['handle'][1:]}/status/{tweet['id']}"
                        })
            except Exception as e:
                logger.warning(f"Error fetching news from {account['handle']}: {e}")
        
        # Sort by recency and engagement
        latest_news.sort(
            key=lambda x: (x['created_at'], x['engagement'].get('like_count', 0)),
            reverse=True
        )
        
        return {
            'symbol': request.symbol,
            'metric': 'influencer_news',
            'news_count': len(latest_news),
            'latest_news': latest_news[:10],  # Top 10
            'sources': [acc['handle'] for acc in news_accounts],
            'timestamp': datetime.now().isoformat(),
        }
    
    async def _fetch_specific_influencer(self, request: DataRequest) -> Dict[str, Any]:
        """Fetch data for a specific influencer"""
        
        handle = request.parameters.get('handle', '@saylor')
        max_results = request.parameters.get('max_results', 10)
        
        # Find influencer in config
        accounts = self.influencers.get('top_bitcoin_twitter_accounts', [])
        influencer = next((acc for acc in accounts if acc['handle'] == handle), None)
        
        if not influencer:
            raise DataNotAvailableError(f"Influencer {handle} not in monitored list")
        
        # Fetch their tweets
        tweets = await self._fetch_user_tweets(handle, max_results=max_results)
        
        return {
            'symbol': request.symbol,
            'handle': handle,
            'name': influencer['name'],
            'specialty': influencer['specialty'],
            'priority': influencer['priority'],
            'weight': influencer['weight'],
            'recent_tweets': tweets,
            'sentiment': self._analyze_sentiment(tweets),
            'engagement_avg': self._calculate_avg_engagement(tweets),
            'timestamp': datetime.now().isoformat(),
        }
    
    async def _fetch_user_tweets(self, handle: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent tweets from a user"""
        
        # Remove @ from handle
        username = handle.lstrip('@')
        
        # First, get user ID
        user_url = f"{self.BASE_URL}/users/by/username/{username}"
        user_params = {
            "user.fields": "public_metrics,verified"
        }
        
        async with self.session.get(user_url, params=user_params) as response:
            self._update_rate_limit(response.headers)
            
            if response.status == 429:
                raise RateLimitError("Twitter rate limit exceeded")
            
            response.raise_for_status()
            user_data = await response.json()
            user_id = user_data['data']['id']
        
        # Fetch user's tweets
        tweets_url = f"{self.BASE_URL}/users/{user_id}/tweets"
        tweets_params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,entities",
            "exclude": "retweets,replies"
        }
        
        async with self.session.get(tweets_url, params=tweets_params) as response:
            self._update_rate_limit(response.headers)
            
            if response.status == 429:
                raise RateLimitError("Twitter rate limit exceeded")
            
            response.raise_for_status()
            data = await response.json()
            
            return data.get('data', [])
    
    def _update_rate_limit(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        if 'x-rate-limit-remaining' in headers:
            self._rate_limit_remaining = int(headers['x-rate-limit-remaining'])
        if 'x-rate-limit-reset' in headers:
            reset_timestamp = int(headers['x-rate-limit-reset'])
            self._rate_limit_reset = datetime.fromtimestamp(reset_timestamp)
    
    def _analyze_sentiment(self, tweets: List[Dict[str, Any]]) -> float:
        """
        Analyze sentiment of tweets.
        Returns score from 0 (bearish) to 1 (bullish).
        
        This is a simple keyword-based analysis.
        For production, use LLM-based sentiment analysis.
        """
        if not tweets:
            return 0.5
        
        bullish_keywords = [
            'bullish', 'moon', 'buying', 'buy', 'accumulate', 'up', 'pump',
            'growth', 'positive', 'strong', 'adoption', 'institutional'
        ]
        bearish_keywords = [
            'bearish', 'dump', 'sell', 'crash', 'down', 'weak', 'negative',
            'correction', 'drop', 'decline', 'fear'
        ]
        
        scores = []
        for tweet in tweets:
            text = tweet.get('text', '').lower()
            
            bullish_count = sum(1 for kw in bullish_keywords if kw in text)
            bearish_count = sum(1 for kw in bearish_keywords if kw in text)
            
            if bullish_count + bearish_count == 0:
                score = 0.5  # Neutral
            else:
                score = bullish_count / (bullish_count + bearish_count)
            
            scores.append(score)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment score"""
        if score >= 0.7:
            return "Very Bullish"
        elif score >= 0.6:
            return "Bullish"
        elif score >= 0.4:
            return "Neutral"
        elif score >= 0.3:
            return "Bearish"
        else:
            return "Very Bearish"
    
    def _interpret_sentiment(self, score: float) -> Dict[str, Any]:
        """Interpret sentiment score"""
        classification = self._classify_sentiment(score)
        
        if score >= 0.7:
            signal = "Strong Buy Signal"
            description = "Influencers are very bullish. High confidence in upward movement."
        elif score >= 0.6:
            signal = "Buy Signal"
            description = "Positive sentiment from influencers. Consider accumulating."
        elif score >= 0.4:
            signal = "Hold"
            description = "Neutral sentiment. No clear directional signal."
        elif score >= 0.3:
            signal = "Caution"
            description = "Negative sentiment emerging. Monitor closely."
        else:
            signal = "Sell Signal"
            description = "Very bearish sentiment. High risk of downward movement."
        
        return {
            'score': score,
            'classification': classification,
            'signal': signal,
            'description': description,
        }
    
    def _is_newsworthy(self, tweet: Dict[str, Any]) -> bool:
        """Check if tweet contains newsworthy content"""
        text = tweet.get('text', '').lower()
        
        news_keywords = [
            'announce', 'breaking', 'news', 'update', 'bought', 'purchased',
            'acquired', 'adoption', 'regulatory', 'government', 'legal tender',
            'institutional', 'treasury', 'billion', 'million BTC'
        ]
        
        return any(keyword in text for keyword in news_keywords)
    
    def _calculate_avg_engagement(self, tweets: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average engagement metrics"""
        if not tweets:
            return {'likes': 0, 'retweets': 0, 'replies': 0}
        
        total_likes = sum(t.get('public_metrics', {}).get('like_count', 0) for t in tweets)
        total_retweets = sum(t.get('public_metrics', {}).get('retweet_count', 0) for t in tweets)
        total_replies = sum(t.get('public_metrics', {}).get('reply_count', 0) for t in tweets)
        
        count = len(tweets)
        
        return {
            'likes': total_likes / count,
            'retweets': total_retweets / count,
            'replies': total_replies / count,
            'total_engagement': (total_likes + total_retweets + total_replies) / count
        }
    
    async def health_check(self) -> bool:
        """Check if Twitter API is available"""
        try:
            await self._ensure_session()
            
            # Simple API test - fetch a known tweet (Jack Dorsey's first tweet)
            url = f"{self.BASE_URL}/tweets/20"
            
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                if response.status != 200:
                    text = await response.text()
                    logger.error(f"Health check failed. Status: {response.status}, Response: {text[:200]}")
                return response.status == 200
        except Exception as e:
            logger.error(f"TwitterIntelligence health check failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def __del__(self):
        """Cleanup session on deletion"""
        if hasattr(self, 'session') and self.session:
            try:
                asyncio.create_task(self._close_session())
            except RuntimeError:
                pass  # Event loop may be closed
