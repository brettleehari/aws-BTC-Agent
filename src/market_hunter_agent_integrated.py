"""
Enhanced Market Hunter Agent with Data Interfaces Integration

This is the integrated version that combines:
1. Agent's autonomous decision-making and learning
2. Data Interfaces module's technical reliability and capability advertisement
3. Hybrid quality scoring (70% technical + 30% agent learning)
4. Rate limit awareness and circuit breaker handling
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
import random

from src.data_interfaces import (
    DataInterfaceManager,
    CapabilityRegistry,
    DataType,
    Capability,
    RequestPriority,
    DataRequest,
    get_manager,
    get_registry
)
from src.source_mapping import (
    LOGICAL_TO_TECHNICAL_MAPPING,
    get_source_requirements,
    get_context_boosted_importance,
    get_preferred_capabilities_for_context
)

logger = logging.getLogger(__name__)


class MarketContext(Enum):
    """Market context types for source selection"""
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    BULLISH_TREND = "bullish_trend"
    BEARISH_TREND = "bearish_trend"
    NEUTRAL = "neutral"


class TradingHours(Enum):
    """Trading hours for geographic optimization"""
    ASIAN = "asian"
    EUROPEAN = "european"
    AMERICAN = "american"
    OVERLAP = "overlap"


class IntegratedMarketHunterAgent:
    """
    Enhanced Market Hunter Agent with Data Interfaces integration.
    
    Combines:
    - Agent's autonomous decision-making
    - Data Interfaces technical reliability
    - Hybrid quality scoring
    - Rate limit awareness
    """
    
    # Logical data sources (agent's view)
    LOGICAL_SOURCES = list(LOGICAL_TO_TECHNICAL_MAPPING.keys())
    
    def __init__(
        self,
        agent_name: str = "market-hunter",
        learning_rate: float = 0.1,
        exploration_rate: float = 0.2,
        technical_weight: float = 0.7,  # 70% technical, 30% learning
        enable_cache: bool = True,
        cache_ttl: int = 60
    ):
        """
        Initialize the integrated agent.
        
        Args:
            agent_name: Name of the agent
            learning_rate: How fast to adapt to new observations (0.0-1.0)
            exploration_rate: Probability of trying underused sources (0.0-1.0)
            technical_weight: Weight for technical scores vs agent learning (0.0-1.0)
            enable_cache: Enable response caching
            cache_ttl: Cache time-to-live in seconds
        """
        self.agent_name = agent_name
        self.learning_rate = learning_rate
        self.exploration_rate = exploration_rate
        self.technical_weight = technical_weight
        self.agent_weight = 1.0 - technical_weight
        
        # Initialize Data Interfaces components with cache configuration
        self.manager = get_manager(cache_ttl=cache_ttl if enable_cache else 60)
        self.registry = get_registry()
        
        # Agent's learned metrics (per logical source)
        self.source_metrics: Dict[str, Dict[str, float]] = {
            source: {
                "success_rate": 0.5,      # % of successful calls
                "quality_score": 0.5,     # % contributing to signals
                "last_used_cycles": 0,    # Cycles since last use
                "total_calls": 0,         # Total calls made
                "successful_calls": 0,    # Successful calls
                "signals_generated": 0    # Signals generated
            }
            for source in self.LOGICAL_SOURCES
        }
        
        # Context-aware learning
        self.context_performance: Dict[str, Dict[str, float]] = {
            context.value: {source: 0.5 for source in self.LOGICAL_SOURCES}
            for context in MarketContext
        }
        
        # Current cycle information
        self.current_cycle = 0
        self.last_query_times: Dict[str, datetime] = {}
        
        # Discover available technical sources
        self._discover_capabilities()
        
        logger.info(
            f"Initialized {agent_name} with {len(self.LOGICAL_SOURCES)} logical sources "
            f"mapped to {len(self.registry.list_sources())} technical sources"
        )
    
    def _discover_capabilities(self):
        """Discover available capabilities from Data Interfaces module"""
        available_sources = self.registry.list_sources()
        all_capabilities = self.registry.get_all_capabilities()
        all_data_types = self.registry.get_all_data_types()
        
        logger.info(f"Discovered {len(available_sources)} technical data sources")
        logger.info(f"Available capabilities: {[c.value for c in all_capabilities]}")
        logger.info(f"Available data types: {[dt.value for dt in all_data_types]}")
        
        # Map logical sources to available technical capabilities
        self.source_mapping: Dict[str, Dict[str, Any]] = {}
        
        for logical_source in self.LOGICAL_SOURCES:
            requirements = get_source_requirements(logical_source)
            
            # Find technical sources that can fulfill requirements
            matching_sources = self.registry.find_sources(
                data_types=requirements["data_types"],
                required_capabilities=requirements["required_capabilities"]
            )
            
            self.source_mapping[logical_source] = {
                "requirements": requirements,
                "matching_technical_sources": matching_sources,  # These are already source names/IDs
                "can_fulfill": len(matching_sources) > 0
            }
            
            if len(matching_sources) == 0:
                logger.warning(
                    f"Logical source '{logical_source}' has no matching technical sources"
                )
    
    def assess_market_context(
        self,
        current_price: float,
        price_24h_ago: float,
        volume_24h: float,
        avg_volume: float
    ) -> MarketContext:
        """
        Assess current market context for source selection.
        
        Args:
            current_price: Current BTC price
            price_24h_ago: BTC price 24h ago
            volume_24h: 24h trading volume
            avg_volume: Average trading volume
            
        Returns:
            Market context enum
        """
        price_change_pct = ((current_price - price_24h_ago) / price_24h_ago) * 100
        volatility = abs(price_change_pct)
        volume_ratio = volume_24h / avg_volume if avg_volume > 0 else 1.0
        
        # High volatility context
        if volatility > 5.0:
            return MarketContext.HIGH_VOLATILITY
        
        # Low volatility context
        if volatility < 2.0 and volume_ratio < 0.8:
            return MarketContext.LOW_VOLATILITY
        
        # Trend-based context
        if price_change_pct > 2.0 and volume_ratio > 1.2:
            return MarketContext.BULLISH_TREND
        elif price_change_pct < -2.0:
            return MarketContext.BEARISH_TREND
        
        return MarketContext.NEUTRAL
    
    def get_trading_hours(self) -> TradingHours:
        """Determine current trading hours based on UTC time"""
        hour = datetime.utcnow().hour
        
        # Asian: 00:00-08:00 UTC
        if 0 <= hour < 8:
            return TradingHours.ASIAN
        # European: 08:00-13:00 UTC
        elif 8 <= hour < 13:
            return TradingHours.EUROPEAN
        # Overlap: 13:00-16:00 UTC
        elif 13 <= hour < 16:
            return TradingHours.OVERLAP
        # American: 16:00-24:00 UTC
        else:
            return TradingHours.AMERICAN
    
    def _get_combined_quality_score(
        self,
        logical_source: str,
        context: MarketContext
    ) -> float:
        """
        Calculate combined quality score from technical and agent learning.
        
        Args:
            logical_source: Logical source name
            context: Current market context
            
        Returns:
            Combined score (0.0-1.0)
        """
        # Get agent's learned score
        agent_score = self.context_performance[context.value].get(logical_source, 0.5)
        
        # Get technical score from Data Interfaces
        technical_score = 0.5  # Default if no technical sources
        
        mapping = self.source_mapping.get(logical_source, {})
        matching_sources = mapping.get("matching_technical_sources", [])
        
        if matching_sources:
            # Use best technical source
            technical_metadata = [
                self.registry.get_source(source_id)
                for source_id in matching_sources
            ]
            
            if technical_metadata:
                # Calculate technical score from metadata
                best_metadata = max(
                    technical_metadata,
                    key=lambda m: m.quality_score if m else 0
                )
                technical_score = best_metadata.quality_score if best_metadata else 0.5
        
        # Combine scores
        combined_score = (
            self.technical_weight * technical_score +
            self.agent_weight * agent_score
        )
        
        return combined_score
    
    def select_sources(
        self,
        context: MarketContext,
        max_sources: int = 6
    ) -> List[str]:
        """
        Select logical sources to query based on context and combined scores.
        
        Args:
            context: Current market context
            max_sources: Maximum number of sources to select
            
        Returns:
            List of selected logical source names
        """
        scores: Dict[str, float] = {}
        
        for logical_source in self.LOGICAL_SOURCES:
            # Skip sources with no technical implementation
            if not self.source_mapping[logical_source]["can_fulfill"]:
                continue
            
            # Start with combined quality score
            base_score = self._get_combined_quality_score(logical_source, context)
            
            # Apply context-specific importance boost
            importance_boost = get_context_boosted_importance(
                logical_source,
                context.value
            )
            score = base_score * importance_boost
            
            # Recency bonus (exploration)
            cycles_since_use = self.source_metrics[logical_source]["last_used_cycles"]
            if cycles_since_use > 5:
                score += 0.1 * min(cycles_since_use / 10, 0.3)
            
            # Exploration: Random chance to boost underused sources
            if random.random() < self.exploration_rate:
                if self.source_metrics[logical_source]["total_calls"] < 10:
                    score += 0.2
            
            scores[logical_source] = score
        
        # Sort by score and select top sources
        sorted_sources = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        selected = [source for source, _ in sorted_sources[:max_sources]]
        
        logger.info(
            f"Selected {len(selected)} sources for context {context.value}: {selected}"
        )
        
        return selected
    
    async def query_source_with_rate_limit_check(
        self,
        logical_source: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query a logical source with rate limit awareness.
        
        Args:
            logical_source: Logical source to query
            parameters: Optional query parameters
            
        Returns:
            Data response or None if rate limited/failed
        """
        # Get requirements and matching technical sources
        requirements = get_source_requirements(logical_source)
        
        if parameters is None:
            parameters = requirements.get("query_params", {})
        
        # Create data request
        request = DataRequest(
            data_types=requirements["data_types"],
            required_capabilities=requirements["required_capabilities"],
            optional_capabilities=requirements.get("optional_capabilities", []),
            priority=requirements.get("priority", RequestPriority.NORMAL),
            parameters=parameters
        )
        
        try:
            # Query through Data Interfaces Manager
            # It handles: source selection, rate limiting, circuit breakers, caching, fallback
            response = await self.manager.query(request)
            
            # Update agent metrics
            self.source_metrics[logical_source]["successful_calls"] += 1
            self.source_metrics[logical_source]["total_calls"] += 1
            
            # Update last query time
            self.last_query_times[logical_source] = datetime.utcnow()
            
            # Extract metadata for learning
            if response.metadata:
                # Use technical quality score for learning
                technical_quality = response.metadata.quality_score
                
                # Update agent's learned quality
                current_quality = self.source_metrics[logical_source]["quality_score"]
                new_quality = (
                    (1 - self.learning_rate) * current_quality +
                    self.learning_rate * technical_quality
                )
                self.source_metrics[logical_source]["quality_score"] = new_quality
            
            return {
                "source": logical_source,
                "data": response.data,
                "technical_source": response.source_id,
                "timestamp": response.timestamp,
                "quality": response.metadata.quality_score if response.metadata else None,
                "from_cache": response.from_cache
            }
            
        except Exception as e:
            logger.warning(f"Failed to query {logical_source}: {str(e)}")
            
            # Update failure metrics
            self.source_metrics[logical_source]["total_calls"] += 1
            
            # Decrease success rate
            current_success = self.source_metrics[logical_source]["success_rate"]
            new_success = (
                (1 - self.learning_rate) * current_success +
                self.learning_rate * 0.0  # Failed
            )
            self.source_metrics[logical_source]["success_rate"] = new_success
            
            return None
    
    async def run_cycle(
        self,
        market_data: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Run one complete agent cycle.
        
        Args:
            market_data: Current market data with keys:
                - current_price
                - price_24h_ago
                - volume_24h
                - avg_volume
                
        Returns:
            Cycle results with queried data and generated signals
        """
        self.current_cycle += 1
        cycle_start = datetime.utcnow()
        
        logger.info(f"Starting cycle {self.current_cycle}")
        
        # Assess market context
        context = self.assess_market_context(
            market_data["current_price"],
            market_data["price_24h_ago"],
            market_data["volume_24h"],
            market_data["avg_volume"]
        )
        
        trading_hours = self.get_trading_hours()
        
        # Determine number of sources based on volatility
        if context == MarketContext.HIGH_VOLATILITY:
            max_sources = 6
        elif context == MarketContext.LOW_VOLATILITY:
            max_sources = 3
        else:
            max_sources = 4
        
        # Select sources
        selected_sources = self.select_sources(context, max_sources)
        
        # Query selected sources
        results = []
        for source in selected_sources:
            result = await self.query_source_with_rate_limit_check(source)
            if result:
                results.append(result)
        
        # Update recency metrics
        for source in self.LOGICAL_SOURCES:
            if source in selected_sources:
                self.source_metrics[source]["last_used_cycles"] = 0
            else:
                self.source_metrics[source]["last_used_cycles"] += 1
        
        # Generate signals (simplified - would have full logic)
        signals = self._generate_signals(results, context)
        
        cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
        
        return {
            "cycle": self.current_cycle,
            "context": context.value,
            "trading_hours": trading_hours.value,
            "sources_selected": selected_sources,
            "sources_queried": len(results),
            "data_points": results,
            "signals_generated": signals,
            "duration_seconds": cycle_duration,
            "timestamp": cycle_start.isoformat()
        }
    
    def _generate_signals(
        self,
        results: List[Dict[str, Any]],
        context: MarketContext
    ) -> List[Dict[str, Any]]:
        """
        Generate signals from query results.
        
        Args:
            results: Query results
            context: Market context
            
        Returns:
            List of generated signals
        """
        signals = []
        
        # This would contain full signal generation logic
        # For now, simplified example
        
        for result in results:
            source = result["source"]
            data = result["data"]
            
            # Example: Whale activity signal
            if source == "whaleMovements" and data:
                whale_count = len(data.get("transactions", []))
                if whale_count > 5:
                    signals.append({
                        "type": "WHALE_ACTIVITY",
                        "severity": "high",
                        "confidence": 0.85,
                        "source": source,
                        "details": f"{whale_count} large transactions detected",
                        "recommended_action": "MONITOR_CLOSELY"
                    })
                    
                    # Update signal generation metric
                    self.source_metrics[source]["signals_generated"] += 1
        
        return signals
    
    def get_source_status(self) -> Dict[str, Any]:
        """Get detailed status of all sources"""
        status = {
            "logical_sources": {},
            "technical_sources": self.registry.list_sources(),
            "manager_stats": self.manager.get_stats()
        }
        
        for source in self.LOGICAL_SOURCES:
            mapping = self.source_mapping[source]
            metrics = self.source_metrics[source]
            
            status["logical_sources"][source] = {
                "can_fulfill": mapping["can_fulfill"],
                "technical_sources": mapping["matching_technical_sources"],
                "agent_metrics": metrics,
                "requirements": {
                    "data_types": [dt.value for dt in mapping["requirements"]["data_types"]],
                    "capabilities": [c.value for c in mapping["requirements"]["required_capabilities"]]
                }
            }
        
        return status
