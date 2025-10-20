"""
Autonomous Market Hunter Agent

A hybrid adaptive learning + goal-oriented agent that:
1. Learns optimal data source selection based on market conditions
2. Generates actionable trading signals for other agents
3. Continuously improves through reinforcement learning
4. Adapts to changing market dynamics

Architecture:
- Adaptive Learning Core: Learns from every cycle
- Goal-Oriented Layer: Optimizes for signal quality and cost
- Context-Aware: Adjusts to market volatility, trend, time
- Multi-Source Integration: Leverages all 7 data sources

Market Conditions Assessment:
- Volatility: HIGH (>5%), MEDIUM (2-5%), LOW (<2%)
- Trend: BULLISH, BEARISH, NEUTRAL
- Volume: HIGH (>120%), NORMAL (80-120%), LOW (<80%)
- Time: ASIAN, EUROPEAN, AMERICAN, OVERLAP

Data Source Mapping:
1. whaleMovements → Blockchain.com (whale tracking)
2. narrativeShifts → NewsAPI + Twitter (sentiment)
3. influencerSignals → Twitter (10 influencers)
4. technicalBreakouts → Technical Indicators (RSI, MACD, BB)
5. macroSignals → Fear & Greed Index
6. arbitrageOpportunities → CoinGecko + Binance + Alpha Vantage
7. institutionalFlows → Blockchain.com (on-chain)
8. derivativesSignals → [To be added]
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics
import random
import logging

# Import our data sources
from .coingecko_interface import CoinGeckoInterface
from .sentiment_interface import SentimentInterface
from .twitter_interface import TwitterInterface
from .newsapi_interface import NewsAPIInterface
from .alphavantage_interface import AlphaVantageInterface
from .blockchain_interface import BlockchainDotComInterface
from .binance_interface import BinanceInterface
from .technical_indicators import TechnicalIndicators
from .sentiment_analyzer import SentimentAnalyzer
from .base_interface import DataRequest
from .metadata import DataType

logger = logging.getLogger(__name__)


class MarketVolatility(Enum):
    """Market volatility levels"""
    HIGH = "high"  # >5% price change
    MEDIUM = "medium"  # 2-5%
    LOW = "low"  # <2%


class MarketTrend(Enum):
    """Market trend direction"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class TradingSession(Enum):
    """Global trading sessions"""
    ASIAN = "asian"  # 00:00-08:00 UTC
    EUROPEAN = "european"  # 08:00-16:00 UTC
    AMERICAN = "american"  # 16:00-00:00 UTC
    OVERLAP = "overlap"  # Multiple sessions active


class SignalSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MarketContext:
    """Current market context assessment"""
    timestamp: datetime
    price: float
    price_change_24h: float  # Percentage
    volatility: MarketVolatility
    trend: MarketTrend
    volume_ratio: float  # Current volume / average volume
    session: TradingSession
    
    # Derived metrics
    is_high_volatility: bool = field(init=False)
    is_trending: bool = field(init=False)
    
    def __post_init__(self):
        self.is_high_volatility = self.volatility == MarketVolatility.HIGH
        self.is_trending = self.trend != MarketTrend.NEUTRAL


@dataclass
class DataSourceMetrics:
    """Performance metrics for a data source"""
    name: str
    
    # Performance metrics
    success_rate: float = 0.5  # % of calls that return data
    signal_quality: float = 0.5  # % that contribute to actionable signals
    avg_latency: float = 1.0  # Average response time (seconds)
    cost_per_call: float = 0.0  # API cost if any
    
    # Learning metrics
    total_calls: int = 0
    successful_calls: int = 0
    quality_signals: int = 0
    last_called: Optional[datetime] = None
    
    # Context relevance scores (updated by learning)
    high_volatility_score: float = 0.5
    low_volatility_score: float = 0.5
    bullish_score: float = 0.5
    bearish_score: float = 0.5
    asian_session_score: float = 0.5
    european_session_score: float = 0.5
    american_session_score: float = 0.5


@dataclass
class MarketSignal:
    """Signal generated for other agents"""
    signal_type: str
    severity: SignalSeverity
    confidence: float  # 0-1
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    recommended_action: Optional[str] = None
    target_agents: List[str] = field(default_factory=list)


class MarketHunterAgent:
    """
    Autonomous Market Hunter Agent
    
    Adaptive learning agent that:
    - Selects optimal data sources based on market conditions
    - Learns from every cycle to improve performance
    - Generates actionable signals for other agents
    - Balances exploration vs exploitation
    - Optimizes for signal quality and cost efficiency
    """
    
    # Learning parameters
    LEARNING_RATE = 0.1  # Weight given to new observations (10%)
    EXPLORATION_RATE = 0.2  # Chance to try underused sources (20%)
    RECENCY_BONUS_HOURS = 6  # Bonus for sources not called in X hours
    
    # Selection parameters
    HIGH_VOLATILITY_SOURCES = 6  # Number of sources in high volatility
    MEDIUM_VOLATILITY_SOURCES = 4
    LOW_VOLATILITY_SOURCES = 3
    
    # Signal thresholds
    WHALE_THRESHOLD_BTC = 100  # Large transaction threshold
    NARRATIVE_COUNT_THRESHOLD = 3  # Multiple bullish narratives
    FUNDING_RATE_THRESHOLD = 0.05  # 5% funding rate
    FEAR_GREED_EXTREME_HIGH = 75
    FEAR_GREED_EXTREME_LOW = 25
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    
    @staticmethod
    def _validate_api_keys():
        """
        Validate all required API keys at startup.
        
        This method MUST be called before initializing any data sources.
        It ensures all required credentials are available and fails fast
        with clear error messages if anything is missing.
        
        Raises:
            ValueError: If any required API keys are missing, with detailed
                       instructions on how to set them.
        """
        import os
        
        missing_keys = []
        
        # Required API keys
        required_keys = {
            'TWITTER_BEARER_TOKEN': 'Twitter API Bearer Token',
            'NEWSAPI_KEY': 'NewsAPI Key',
            'ALPHA_VANTAGE_API_KEY': 'Alpha Vantage API Key'
        }
        
        for env_var, description in required_keys.items():
            if not os.getenv(env_var):
                missing_keys.append(f"  - {env_var}: {description}")
        
        if missing_keys:
            error_msg = (
                "\n" + "="*70 + "\n"
                "❌ MISSING REQUIRED API KEYS\n"
                "="*70 + "\n"
                "The Market Hunter Agent requires the following API keys to function:\n\n"
                + "\n".join(missing_keys) + "\n\n"
                "Please set these environment variables before starting the agent:\n\n"
                "  export TWITTER_BEARER_TOKEN='your_twitter_token'\n"
                "  export NEWSAPI_KEY='your_newsapi_key'\n"
                "  export ALPHA_VANTAGE_API_KEY='your_alphavantage_key'\n\n"
                "Or add them to your .env file:\n\n"
                "  TWITTER_BEARER_TOKEN=your_twitter_token\n"
                "  NEWSAPI_KEY=your_newsapi_key\n"
                "  ALPHA_VANTAGE_API_KEY=your_alphavantage_key\n\n"
                "Then load with: python-dotenv or source .env\n"
                "="*70
            )
            raise ValueError(error_msg)
        
        logger.info("✓ All required API keys validated")
    
    def __init__(self):
        """
        Initialize the Market Hunter Agent.
        
        Validates all required API keys at startup. Fails fast with clear
        error messages if any keys are missing. This ensures the agent
        is fully operational before starting any cycles.
        
        Required Environment Variables:
        - TWITTER_BEARER_TOKEN: Twitter API access
        - NEWSAPI_KEY: NewsAPI access
        - ALPHA_VANTAGE_API_KEY: Alpha Vantage access
        
        Optional (free APIs, no keys needed):
        - CoinGecko, Fear & Greed, Blockchain.com, Binance
        
        Raises:
            ValueError: If any required API keys are missing
        """
        
        # Validate required API keys before initializing anything
        self._validate_api_keys()
        
        # Initialize data source interfaces
        # These should all succeed after validation
        self.coingecko = CoinGeckoInterface()
        self.fear_greed = SentimentInterface()
        self.twitter = TwitterInterface()
        self.newsapi = NewsAPIInterface()
        self.alphavantage = AlphaVantageInterface()
        self.blockchain = BlockchainDotComInterface()
        self.binance = BinanceInterface()
        self.technical_indicators = TechnicalIndicators()
        self.sentiment_analyzer = SentimentAnalyzer(
            newsapi_interface=self.newsapi,
            twitter_interface=self.twitter,
            sentiment_interface=self.fear_greed
        )
        
        # Initialize source metrics (with learning)
        self.source_metrics: Dict[str, DataSourceMetrics] = {
            "whaleMovements": DataSourceMetrics("whaleMovements"),
            "narrativeShifts": DataSourceMetrics("narrativeShifts"),
            "influencerSignals": DataSourceMetrics("influencerSignals"),
            "technicalBreakouts": DataSourceMetrics("technicalBreakouts"),
            "macroSignals": DataSourceMetrics("macroSignals"),
            "arbitrageOpportunities": DataSourceMetrics("arbitrageOpportunities"),
            "institutionalFlows": DataSourceMetrics("institutionalFlows"),
        }
        
        # Historical data storage
        self.execution_history: List[Dict[str, Any]] = []
        self.signal_history: List[MarketSignal] = []
        self.market_context_history: List[MarketContext] = []
        self.price_history: List[float] = []
        
        # State
        self.current_context: Optional[MarketContext] = None
        self.cycle_count = 0
        
        logger.info("Market Hunter Agent initialized with 7 data sources")
    
    async def assess_market_context(self) -> MarketContext:
        """
        Assess current market conditions.
        
        Returns:
            MarketContext with volatility, trend, volume, session
        """
        try:
            # Fetch current price
            request = DataRequest(data_type=DataType.PRICE, parameters={"symbol": "BTC"})
            price_response = await self.coingecko.fetch(request)
            
            if not price_response.success:
                raise Exception("Failed to fetch price data")
            
            current_price = price_response.data.get("price", 0)
            self.price_history.append(current_price)
            
            # Keep last 24 hours of prices (1440 minutes at 1/min)
            if len(self.price_history) > 1440:
                self.price_history = self.price_history[-1440:]
            
            # Calculate 24h price change
            if len(self.price_history) > 1:
                price_24h_ago = self.price_history[0] if len(self.price_history) <= 1440 else self.price_history[-1440]
                price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
            else:
                price_change_24h = 0.0
            
            # Determine volatility
            if abs(price_change_24h) > 5:
                volatility = MarketVolatility.HIGH
            elif abs(price_change_24h) > 2:
                volatility = MarketVolatility.MEDIUM
            else:
                volatility = MarketVolatility.LOW
            
            # Determine trend
            if price_change_24h > 2:
                trend = MarketTrend.BULLISH
            elif price_change_24h < -2:
                trend = MarketTrend.BEARISH
            else:
                trend = MarketTrend.NEUTRAL
            
            # Get volume (mock for now, would fetch from exchange)
            volume_ratio = 1.0  # Normal volume
            
            # Determine trading session
            current_hour = datetime.utcnow().hour
            if 0 <= current_hour < 8:
                session = TradingSession.ASIAN
            elif 8 <= current_hour < 16:
                session = TradingSession.EUROPEAN
            else:
                session = TradingSession.AMERICAN
            
            context = MarketContext(
                timestamp=datetime.now(),
                price=current_price,
                price_change_24h=price_change_24h,
                volatility=volatility,
                trend=trend,
                volume_ratio=volume_ratio,
                session=session
            )
            
            self.current_context = context
            self.market_context_history.append(context)
            
            logger.info(
                f"Market Context: Price=${current_price:,.2f}, "
                f"Change={price_change_24h:+.2f}%, "
                f"Volatility={volatility.value}, "
                f"Trend={trend.value}, "
                f"Session={session.value}"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to assess market context: {e}")
            # Return default context
            return MarketContext(
                timestamp=datetime.now(),
                price=0,
                price_change_24h=0,
                volatility=MarketVolatility.MEDIUM,
                trend=MarketTrend.NEUTRAL,
                volume_ratio=1.0,
                session=TradingSession.AMERICAN
            )
    
    def calculate_source_scores(self, context: MarketContext) -> Dict[str, float]:
        """
        Calculate relevance scores for each data source based on context.
        
        Scoring factors:
        - Base success rate
        - Context relevance (volatility, trend, session)
        - Recency bonus (not called recently)
        - Exploration bonus (random exploration)
        - Signal quality history
        
        Returns:
            Dict mapping source name to score (0-1)
        """
        scores = {}
        now = datetime.now()
        
        for source_name, metrics in self.source_metrics.items():
            # Base score from historical performance
            base_score = (metrics.success_rate * 0.4 + metrics.signal_quality * 0.6)
            
            # Context relevance
            context_score = 0.0
            
            # Volatility relevance
            if context.volatility == MarketVolatility.HIGH:
                context_score += metrics.high_volatility_score * 0.3
            else:
                context_score += metrics.low_volatility_score * 0.3
            
            # Trend relevance
            if context.trend == MarketTrend.BULLISH:
                context_score += metrics.bullish_score * 0.3
            elif context.trend == MarketTrend.BEARISH:
                context_score += metrics.bearish_score * 0.3
            else:
                context_score += 0.15  # Neutral
            
            # Session relevance
            if context.session == TradingSession.ASIAN:
                context_score += metrics.asian_session_score * 0.2
            elif context.session == TradingSession.EUROPEAN:
                context_score += metrics.european_session_score * 0.2
            elif context.session == TradingSession.AMERICAN:
                context_score += metrics.american_session_score * 0.2
            
            # Recency bonus (encourage diversity)
            recency_bonus = 0.0
            if metrics.last_called:
                hours_since = (now - metrics.last_called).total_seconds() / 3600
                if hours_since > self.RECENCY_BONUS_HOURS:
                    recency_bonus = min(0.2, hours_since / (self.RECENCY_BONUS_HOURS * 2))
            else:
                recency_bonus = 0.2  # Never called
            
            # Exploration bonus (random chance)
            exploration_bonus = 0.0
            if random.random() < self.EXPLORATION_RATE:
                exploration_bonus = 0.1
            
            # Combined score
            final_score = base_score + context_score + recency_bonus + exploration_bonus
            final_score = max(0.0, min(1.0, final_score))  # Clamp to 0-1
            
            scores[source_name] = final_score
            
            logger.debug(
                f"{source_name}: base={base_score:.2f}, context={context_score:.2f}, "
                f"recency={recency_bonus:.2f}, explore={exploration_bonus:.2f}, "
                f"final={final_score:.2f}"
            )
        
        return scores
    
    def select_data_sources(
        self,
        scores: Dict[str, float],
        context: MarketContext
    ) -> List[str]:
        """
        Select top N data sources based on scores and volatility.
        
        Args:
            scores: Relevance scores for each source
            context: Current market context
            
        Returns:
            List of selected source names
        """
        # Determine how many sources to query
        if context.volatility == MarketVolatility.HIGH:
            num_sources = self.HIGH_VOLATILITY_SOURCES
        elif context.volatility == MarketVolatility.MEDIUM:
            num_sources = self.MEDIUM_VOLATILITY_SOURCES
        else:
            num_sources = self.LOW_VOLATILITY_SOURCES
        
        # Sort by score and select top N
        sorted_sources = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [name for name, score in sorted_sources[:num_sources]]
        
        logger.info(
            f"Selected {len(selected)} sources for {context.volatility.value} volatility: "
            f"{', '.join(selected)}"
        )
        
        return selected
    
    async def query_data_sources(
        self,
        selected_sources: List[str],
        context: MarketContext
    ) -> Dict[str, Any]:
        """
        Query selected data sources and collect results.
        
        Args:
            selected_sources: List of source names to query
            context: Current market context
            
        Returns:
            Dict with results from each source
        """
        results = {}
        start_time = datetime.now()
        
        # Create tasks for parallel execution
        tasks = []
        source_map = {}
        
        for source in selected_sources:
            if source == "whaleMovements":
                task = self._query_whale_movements()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "narrativeShifts":
                task = self._query_narrative_shifts()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "influencerSignals":
                task = self._query_influencer_signals()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "technicalBreakouts":
                task = self._query_technical_breakouts()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "macroSignals":
                task = self._query_macro_signals()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "arbitrageOpportunities":
                task = self._query_arbitrage_opportunities()
                tasks.append(task)
                source_map[len(tasks)-1] = source
                
            elif source == "institutionalFlows":
                task = self._query_institutional_flows()
                tasks.append(task)
                source_map[len(tasks)-1] = source
        
        # Execute all queries in parallel
        query_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and update metrics
        for idx, result in enumerate(query_results):
            source = source_map[idx]
            metrics = self.source_metrics[source]
            
            # Update call statistics
            metrics.total_calls += 1
            metrics.last_called = datetime.now()
            
            if isinstance(result, Exception):
                logger.error(f"{source} query failed: {result}")
                results[source] = {"error": str(result), "success": False}
            elif result and result.get("data"):
                metrics.successful_calls += 1
                metrics.success_rate = metrics.successful_calls / metrics.total_calls
                results[source] = result
            else:
                results[source] = {"success": False, "data": None}
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Queried {len(selected_sources)} sources in {elapsed:.2f}s")
        
        return results
    
    async def _query_whale_movements(self) -> Dict[str, Any]:
        """Query Blockchain.com for whale transactions"""
        try:
            request = DataRequest(
                data_type=DataType.WHALE_TRANSACTIONS,
                parameters={"threshold_btc": self.WHALE_THRESHOLD_BTC}
            )
            response = await self.blockchain.fetch(request)
            
            if response.success:
                return {
                    "success": True,
                    "data": response.data,
                    "source": "Blockchain.com"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Whale movements query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_narrative_shifts(self) -> Dict[str, Any]:
        """Query NewsAPI + Twitter for sentiment trends"""
        try:
            sentiment = await self.sentiment_analyzer.analyze(
                symbol="BTC",
                include_trends=True
            )
            
            if sentiment and sentiment.composite_score is not None:
                return {
                    "success": True,
                    "data": {
                        "sentiment_score": sentiment.composite_score,
                        "sentiment_label": sentiment.sentiment_label,
                        "trend_24h": sentiment.trend_24h,
                        "confidence": sentiment.confidence,
                        "sources": sentiment.sources_used
                    },
                    "source": "Sentiment Analyzer"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Narrative shifts query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_influencer_signals(self) -> Dict[str, Any]:
        """Query Twitter for influencer activity"""
        try:
            request = DataRequest(
                data_type=DataType.INFLUENCER_ACTIVITY,
                parameters={"symbol": "BTC"}
            )
            response = await self.twitter.fetch(request)
            
            if response.success:
                return {
                    "success": True,
                    "data": response.data,
                    "source": "Twitter"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Influencer signals query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_technical_breakouts(self) -> Dict[str, Any]:
        """Query technical indicators for breakout signals"""
        try:
            if len(self.price_history) < 50:
                return {"success": False, "error": "Insufficient price history"}
            
            signals = self.technical_indicators.generate_trading_signals(self.price_history)
            
            if "error" not in signals:
                return {
                    "success": True,
                    "data": signals,
                    "source": "Technical Indicators"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Technical breakouts query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_macro_signals(self) -> Dict[str, Any]:
        """Query Fear & Greed Index"""
        try:
            request = DataRequest(
                data_type=DataType.SOCIAL_SENTIMENT,
                parameters={}
            )
            response = await self.fear_greed.fetch(request)
            
            if response.success:
                return {
                    "success": True,
                    "data": response.data,
                    "source": "Fear & Greed Index"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Macro signals query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_arbitrage_opportunities(self) -> Dict[str, Any]:
        """Query multiple exchanges for price discrepancies"""
        try:
            # Fetch prices from multiple sources
            tasks = [
                self.coingecko.fetch(DataRequest(data_type=DataType.PRICE, parameters={"symbol": "BTC"})),
                self.binance.fetch(DataRequest(data_type=DataType.PRICE, parameters={"symbol": "BTC"})),
                self.alphavantage.fetch(DataRequest(data_type=DataType.PRICE, parameters={"symbol": "BTC"}))
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            prices = []
            for result in results:
                if not isinstance(result, Exception) and result.success:
                    price = result.data.get("price")
                    if price:
                        prices.append(price)
            
            if len(prices) >= 2:
                max_price = max(prices)
                min_price = min(prices)
                spread = ((max_price - min_price) / min_price) * 100
                
                return {
                    "success": True,
                    "data": {
                        "max_price": max_price,
                        "min_price": min_price,
                        "spread_percent": spread,
                        "opportunity": spread > 0.5  # 0.5% spread threshold
                    },
                    "source": "Multi-Exchange"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Arbitrage opportunities query failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _query_institutional_flows(self) -> Dict[str, Any]:
        """Query Blockchain.com for institutional-size flows"""
        try:
            request = DataRequest(
                data_type=DataType.ON_CHAIN,
                parameters={}
            )
            response = await self.blockchain.fetch(request)
            
            if response.success:
                return {
                    "success": True,
                    "data": response.data,
                    "source": "Blockchain.com"
                }
            return {"success": False}
            
        except Exception as e:
            logger.error(f"Institutional flows query failed: {e}")
            return {"success": False, "error": str(e)}
    
    def generate_signals(
        self,
        query_results: Dict[str, Any],
        context: MarketContext
    ) -> List[MarketSignal]:
        """
        Generate actionable signals based on query results.
        
        Args:
            query_results: Results from data sources
            context: Current market context
            
        Returns:
            List of MarketSignal objects
        """
        signals = []
        
        # Process each source result
        for source, result in query_results.items():
            if not result.get("success"):
                continue
            
            data = result.get("data", {})
            
            # Whale activity signals
            if source == "whaleMovements" and data:
                # Check for large transactions
                whale_txs = data.get("whale_transactions", [])
                if len(whale_txs) > 0:
                    total_btc = sum(tx.get("amount", 0) for tx in whale_txs)
                    signals.append(MarketSignal(
                        signal_type="WHALE_ACTIVITY",
                        severity=SignalSeverity.HIGH,
                        confidence=0.8,
                        message=f"{len(whale_txs)} whale transactions detected ({total_btc:.2f} BTC)",
                        data={"transactions": whale_txs[:5]},  # Top 5
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="MONITOR",
                        target_agents=["bitcoin-orchestrator", "risk-manager"]
                    ))
            
            # Sentiment/narrative signals
            elif source == "narrativeShifts" and data:
                sentiment_score = data.get("sentiment_score", 0)
                sentiment_label = data.get("sentiment_label", "NEUTRAL")
                
                if sentiment_label in ["BULLISH", "EXTREME_BULLISH"]:
                    signals.append(MarketSignal(
                        signal_type="POSITIVE_NARRATIVE",
                        severity=SignalSeverity.MEDIUM,
                        confidence=data.get("confidence", 0.5),
                        message=f"Bullish sentiment detected: {sentiment_label}",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="CONSIDER_LONG",
                        target_agents=["bitcoin-orchestrator"]
                    ))
                elif sentiment_label in ["BEARISH", "EXTREME_BEARISH"]:
                    signals.append(MarketSignal(
                        signal_type="NEGATIVE_NARRATIVE",
                        severity=SignalSeverity.MEDIUM,
                        confidence=data.get("confidence", 0.5),
                        message=f"Bearish sentiment detected: {sentiment_label}",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="CONSIDER_SHORT",
                        target_agents=["bitcoin-orchestrator"]
                    ))
            
            # Technical breakout signals
            elif source == "technicalBreakouts" and data:
                composite_signal = data.get("composite_signal", "HOLD")
                composite_score = data.get("composite_score", 0)
                
                if composite_signal in ["STRONG_BUY", "STRONG_SELL"]:
                    signals.append(MarketSignal(
                        signal_type="TECHNICAL_BREAKOUT",
                        severity=SignalSeverity.HIGH,
                        confidence=abs(composite_score),
                        message=f"Technical signal: {composite_signal}",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action=composite_signal.replace("STRONG_", ""),
                        target_agents=["bitcoin-orchestrator", "trading-executor"]
                    ))
            
            # Macro signals (Fear & Greed)
            elif source == "macroSignals" and data:
                fg_value = data.get("value", 50)
                
                if fg_value >= self.FEAR_GREED_EXTREME_HIGH:
                    signals.append(MarketSignal(
                        signal_type="EXTREME_GREED",
                        severity=SignalSeverity.MEDIUM,
                        confidence=0.7,
                        message=f"Extreme greed detected: {fg_value}/100",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="CAUTION",
                        target_agents=["risk-manager"]
                    ))
                elif fg_value <= self.FEAR_GREED_EXTREME_LOW:
                    signals.append(MarketSignal(
                        signal_type="EXTREME_FEAR",
                        severity=SignalSeverity.MEDIUM,
                        confidence=0.7,
                        message=f"Extreme fear detected: {fg_value}/100",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="OPPORTUNITY",
                        target_agents=["bitcoin-orchestrator"]
                    ))
            
            # Arbitrage opportunities
            elif source == "arbitrageOpportunities" and data:
                if data.get("opportunity"):
                    spread = data.get("spread_percent", 0)
                    signals.append(MarketSignal(
                        signal_type="ARBITRAGE_OPPORTUNITY",
                        severity=SignalSeverity.LOW,
                        confidence=0.9,
                        message=f"Price spread detected: {spread:.2f}%",
                        data=data,
                        timestamp=datetime.now(),
                        source=source,
                        recommended_action="ARBITRAGE",
                        target_agents=["trading-executor"]
                    ))
        
        # Store signals
        self.signal_history.extend(signals)
        
        logger.info(f"Generated {len(signals)} signals from {len(query_results)} sources")
        
        return signals
    
    def update_learning_metrics(
        self,
        selected_sources: List[str],
        query_results: Dict[str, Any],
        signals: List[MarketSignal],
        context: MarketContext
    ):
        """
        Update learning metrics based on cycle outcomes.
        
        Uses exponential moving average:
        new_metric = (1 - α) × old_metric + α × observation
        
        Args:
            selected_sources: Sources queried this cycle
            query_results: Results from queries
            signals: Signals generated
            context: Market context
        """
        # Map signals back to sources
        signal_sources = {signal.source for signal in signals}
        
        for source in selected_sources:
            metrics = self.source_metrics[source]
            result = query_results.get(source, {})
            
            # Update signal quality if this source contributed
            if source in signal_sources:
                metrics.quality_signals += 1
                new_quality = 1.0  # Generated a signal
            else:
                new_quality = 0.0  # No signal generated
            
            # Update with learning rate
            metrics.signal_quality = (
                (1 - self.LEARNING_RATE) * metrics.signal_quality +
                self.LEARNING_RATE * new_quality
            )
            
            # Update context-specific scores
            if context.volatility == MarketVolatility.HIGH:
                observation = 1.0 if result.get("success") else 0.0
                metrics.high_volatility_score = (
                    (1 - self.LEARNING_RATE) * metrics.high_volatility_score +
                    self.LEARNING_RATE * observation
                )
            else:
                observation = 1.0 if result.get("success") else 0.0
                metrics.low_volatility_score = (
                    (1 - self.LEARNING_RATE) * metrics.low_volatility_score +
                    self.LEARNING_RATE * observation
                )
            
            # Update trend scores
            if context.trend == MarketTrend.BULLISH:
                observation = 1.0 if source in signal_sources else 0.5
                metrics.bullish_score = (
                    (1 - self.LEARNING_RATE) * metrics.bullish_score +
                    self.LEARNING_RATE * observation
                )
            elif context.trend == MarketTrend.BEARISH:
                observation = 1.0 if source in signal_sources else 0.5
                metrics.bearish_score = (
                    (1 - self.LEARNING_RATE) * metrics.bearish_score +
                    self.LEARNING_RATE * observation
                )
            
            # Update session scores
            observation = 1.0 if result.get("success") else 0.5
            if context.session == TradingSession.ASIAN:
                metrics.asian_session_score = (
                    (1 - self.LEARNING_RATE) * metrics.asian_session_score +
                    self.LEARNING_RATE * observation
                )
            elif context.session == TradingSession.EUROPEAN:
                metrics.european_session_score = (
                    (1 - self.LEARNING_RATE) * metrics.european_session_score +
                    self.LEARNING_RATE * observation
                )
            elif context.session == TradingSession.AMERICAN:
                metrics.american_session_score = (
                    (1 - self.LEARNING_RATE) * metrics.american_session_score +
                    self.LEARNING_RATE * observation
                )
        
        logger.debug(f"Updated learning metrics for {len(selected_sources)} sources")
    
    async def run_cycle(self) -> Dict[str, Any]:
        """
        Run one complete Market Hunter cycle.
        
        Process:
        1. Assess market context
        2. Calculate source scores
        3. Select optimal sources
        4. Query selected sources
        5. Generate signals
        6. Update learning metrics
        7. Log execution
        
        Returns:
            Dict with cycle results and statistics
        """
        cycle_start = datetime.now()
        self.cycle_count += 1
        
        logger.info(f"\n{'='*70}")
        logger.info(f"Market Hunter Cycle #{self.cycle_count} - {cycle_start}")
        logger.info(f"{'='*70}")
        
        try:
            # Step 1: Assess market context
            context = await self.assess_market_context()
            
            # Step 2: Calculate source scores
            scores = self.calculate_source_scores(context)
            
            # Step 3: Select optimal sources
            selected_sources = self.select_data_sources(scores, context)
            
            # Step 4: Query selected sources
            query_results = await self.query_data_sources(selected_sources, context)
            
            # Step 5: Generate signals
            signals = self.generate_signals(query_results, context)
            
            # Step 6: Update learning metrics
            self.update_learning_metrics(selected_sources, query_results, signals, context)
            
            # Step 7: Log execution
            elapsed = (datetime.now() - cycle_start).total_seconds()
            
            execution_log = {
                "cycle": self.cycle_count,
                "timestamp": cycle_start,
                "duration_seconds": elapsed,
                "context": {
                    "price": context.price,
                    "volatility": context.volatility.value,
                    "trend": context.trend.value,
                    "session": context.session.value
                },
                "selected_sources": selected_sources,
                "scores": scores,
                "successful_queries": sum(1 for r in query_results.values() if r.get("success")),
                "signals_generated": len(signals),
                "signals": [
                    {
                        "type": s.signal_type,
                        "severity": s.severity.value,
                        "confidence": s.confidence,
                        "message": s.message
                    }
                    for s in signals
                ]
            }
            
            self.execution_history.append(execution_log)
            
            logger.info(f"\nCycle #{self.cycle_count} Complete:")
            logger.info(f"  Duration: {elapsed:.2f}s")
            logger.info(f"  Successful Queries: {execution_log['successful_queries']}/{len(selected_sources)}")
            logger.info(f"  Signals Generated: {len(signals)}")
            for signal in signals:
                logger.info(f"    • {signal.signal_type}: {signal.message}")
            
            return execution_log
            
        except Exception as e:
            logger.error(f"Cycle #{self.cycle_count} failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "cycle": self.cycle_count,
                "timestamp": cycle_start,
                "error": str(e),
                "success": False
            }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        Returns:
            Dict with statistics and metrics
        """
        if not self.execution_history:
            return {"error": "No execution history"}
        
        # Source performance
        source_stats = {}
        for name, metrics in self.source_metrics.items():
            source_stats[name] = {
                "success_rate": f"{metrics.success_rate:.2%}",
                "signal_quality": f"{metrics.signal_quality:.2%}",
                "total_calls": metrics.total_calls,
                "quality_signals": metrics.quality_signals,
                "last_called": metrics.last_called.isoformat() if metrics.last_called else None
            }
        
        # Cycle statistics
        total_signals = sum(len(e.get("signals", [])) for e in self.execution_history)
        avg_duration = statistics.mean(e.get("duration_seconds", 0) for e in self.execution_history)
        
        # Signal type distribution
        signal_types = {}
        for signal in self.signal_history:
            signal_types[signal.signal_type] = signal_types.get(signal.signal_type, 0) + 1
        
        return {
            "cycles_completed": self.cycle_count,
            "total_signals_generated": total_signals,
            "avg_cycle_duration": f"{avg_duration:.2f}s",
            "source_performance": source_stats,
            "signal_distribution": signal_types,
            "market_context_history_size": len(self.market_context_history),
            "price_history_size": len(self.price_history)
        }
