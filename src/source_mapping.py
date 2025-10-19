"""
Source Mapping Configuration

Maps Market Hunter Agent's logical data sources to Data Interfaces module's
technical capabilities and data types.
"""

from src.data_interfaces import DataType, Capability, RequestPriority


# Mapping between agent's logical sources and technical requirements
LOGICAL_TO_TECHNICAL_MAPPING = {
    # Whale Movements - Track large Bitcoin transactions
    "whaleMovements": {
        "description": "Large on-chain transactions (>100 BTC transfers)",
        "data_types": [DataType.WHALE_TRANSACTIONS, DataType.ON_CHAIN],
        "required_capabilities": [Capability.WHALE_TRACKING],
        "optional_capabilities": [Capability.REAL_TIME, Capability.HISTORICAL],
        "priority": RequestPriority.HIGH,
        "importance_score": 0.95,  # High importance for whale activity
        "query_params": {
            "threshold": 100_000_000,  # $100M USD
            "timeframe": "1h"
        }
    },
    
    # Narrative Shifts - Social media and sentiment changes
    "narrativeShifts": {
        "description": "Social media trends and sentiment shifts",
        "data_types": [DataType.SOCIAL_SENTIMENT],
        "required_capabilities": [Capability.SENTIMENT_ANALYSIS],
        "optional_capabilities": [Capability.REAL_TIME, Capability.AGGREGATION],
        "priority": RequestPriority.NORMAL,
        "importance_score": 0.75,
        "query_params": {
            "metric": "fear_greed",
            "timeframe": "7d"
        }
    },
    
    # Arbitrage Opportunities - Cross-exchange price differences
    "arbitrageOpportunities": {
        "description": "Price spreads across exchanges",
        "data_types": [DataType.PRICE, DataType.VOLUME],
        "required_capabilities": [Capability.MULTI_EXCHANGE, Capability.REAL_TIME],
        "optional_capabilities": [Capability.AGGREGATION],
        "priority": RequestPriority.CRITICAL,
        "importance_score": 0.85,
        "query_params": {
            "vs_currency": "usd",
            "exchanges": ["binance", "coinbase", "kraken"]
        }
    },
    
    # Influencer Signals - Technical analysis from traders
    "influencerSignals": {
        "description": "Trading signals from influencers and analysts",
        "data_types": [DataType.SOCIAL_SENTIMENT, DataType.NEWS],
        "required_capabilities": [Capability.SENTIMENT_ANALYSIS],
        "optional_capabilities": [Capability.REAL_TIME],
        "priority": RequestPriority.NORMAL,
        "importance_score": 0.70,
        "query_params": {
            "source": "twitter",
            "influencers": ["top_traders"]
        }
    },
    
    # Technical Breakouts - Chart patterns and indicators
    "technicalBreakouts": {
        "description": "Technical analysis breakouts and patterns",
        "data_types": [DataType.PRICE, DataType.VOLUME],
        "required_capabilities": [Capability.HISTORICAL, Capability.TIME_SERIES],
        "optional_capabilities": [Capability.REAL_TIME],
        "priority": RequestPriority.NORMAL,
        "importance_score": 0.80,
        "query_params": {
            "timeframe": "1d",
            "indicators": ["RSI", "MACD", "Bollinger"]
        }
    },
    
    # Institutional Flows - Large holder movements
    "institutionalFlows": {
        "description": "Large institutional Bitcoin movements",
        "data_types": [DataType.EXCHANGE_FLOWS, DataType.ON_CHAIN, DataType.WHALE_TRANSACTIONS],
        "required_capabilities": [Capability.EXCHANGE_MONITORING, Capability.WHALE_TRACKING],
        "optional_capabilities": [Capability.ADVANCED_ANALYTICS],
        "priority": RequestPriority.HIGH,
        "importance_score": 0.90,
        "query_params": {
            "metric": "net_flows",
            "min_size": 50_000_000  # $50M USD
        }
    },
    
    # Derivatives Signals - Futures, funding rates, liquidations
    "derivativesSignals": {
        "description": "Derivatives market signals (funding, liquidations)",
        "data_types": [DataType.DERIVATIVES, DataType.ON_CHAIN],
        "required_capabilities": [Capability.DERIVATIVES_TRACKING],
        "optional_capabilities": [Capability.REAL_TIME, Capability.ADVANCED_ANALYTICS],
        "priority": RequestPriority.HIGH,
        "importance_score": 0.85,
        "query_params": {
            "metrics": ["funding_rate", "open_interest", "liquidations"]
        }
    },
    
    # Macro Signals - Fear & Greed, market sentiment
    "macroSignals": {
        "description": "Macro market sentiment and fear/greed indicators",
        "data_types": [DataType.SOCIAL_SENTIMENT],
        "required_capabilities": [Capability.SENTIMENT_ANALYSIS],
        "optional_capabilities": [Capability.HISTORICAL, Capability.TIME_SERIES],
        "priority": RequestPriority.NORMAL,
        "importance_score": 0.75,
        "query_params": {
            "metric": "fear_greed",
            "timeframe": "30d"
        }
    }
}


# Context-specific source priorities
CONTEXT_PRIORITIES = {
    # High volatility - prioritize real-time data
    "high_volatility": {
        "preferred_capabilities": [
            Capability.REAL_TIME,
            Capability.WHALE_TRACKING,
            Capability.DERIVATIVES_TRACKING
        ],
        "source_boost": {
            "whaleMovements": 1.2,
            "derivativesSignals": 1.3,
            "institutionalFlows": 1.2
        }
    },
    
    # Bullish trend - focus on institutional and influencer activity
    "bullish_trend": {
        "preferred_capabilities": [
            Capability.SENTIMENT_ANALYSIS,
            Capability.EXCHANGE_MONITORING
        ],
        "source_boost": {
            "institutionalFlows": 1.3,
            "influencerSignals": 1.2,
            "narrativeShifts": 1.1
        }
    },
    
    # Bearish trend - watch for whale exits and derivative pressure
    "bearish_trend": {
        "preferred_capabilities": [
            Capability.WHALE_TRACKING,
            Capability.DERIVATIVES_TRACKING,
            Capability.EXCHANGE_MONITORING
        ],
        "source_boost": {
            "whaleMovements": 1.3,
            "derivativesSignals": 1.3,
            "institutionalFlows": 1.2
        }
    },
    
    # Low volatility - focus on building narratives and positioning
    "low_volatility": {
        "preferred_capabilities": [
            Capability.SENTIMENT_ANALYSIS,
            Capability.HISTORICAL
        ],
        "source_boost": {
            "narrativeShifts": 1.2,
            "macroSignals": 1.1,
            "influencerSignals": 1.1
        }
    }
}


def get_source_requirements(logical_source: str) -> dict:
    """
    Get technical requirements for a logical source.
    
    Args:
        logical_source: Name of the logical data source
        
    Returns:
        Dictionary with data types, capabilities, and parameters
    """
    if logical_source not in LOGICAL_TO_TECHNICAL_MAPPING:
        raise ValueError(f"Unknown logical source: {logical_source}")
    
    return LOGICAL_TO_TECHNICAL_MAPPING[logical_source].copy()


def get_context_boosted_importance(logical_source: str, context: str) -> float:
    """
    Get importance score with context-specific boost.
    
    Args:
        logical_source: Name of the logical data source
        context: Context key (e.g., "high_volatility", "bullish_trend")
        
    Returns:
        Boosted importance score
    """
    base_importance = LOGICAL_TO_TECHNICAL_MAPPING[logical_source]["importance_score"]
    
    if context in CONTEXT_PRIORITIES:
        boost = CONTEXT_PRIORITIES[context]["source_boost"].get(logical_source, 1.0)
        return min(1.0, base_importance * boost)
    
    return base_importance


def get_preferred_capabilities_for_context(context: str) -> list:
    """
    Get preferred capabilities for a given market context.
    
    Args:
        context: Context key
        
    Returns:
        List of preferred Capability enums
    """
    if context in CONTEXT_PRIORITIES:
        return CONTEXT_PRIORITIES[context]["preferred_capabilities"]
    
    return []


# Export all mappings
__all__ = [
    'LOGICAL_TO_TECHNICAL_MAPPING',
    'CONTEXT_PRIORITIES',
    'get_source_requirements',
    'get_context_boosted_importance',
    'get_preferred_capabilities_for_context',
]
