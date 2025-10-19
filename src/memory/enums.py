"""
Enumerations for the Agent Memory System

Defines all enum types used across the memory and decision logging system.
"""

from enum import Enum


class DecisionType(Enum):
    """Types of decisions that agents can make"""
    SOURCE_SELECTION = "SOURCE_SELECTION"
    QUERY_EXECUTION = "QUERY_EXECUTION"
    SIGNAL_GENERATION = "SIGNAL_GENERATION"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    TRADE_EXECUTION = "TRADE_EXECUTION"
    PORTFOLIO_ADJUSTMENT = "PORTFOLIO_ADJUSTMENT"
    STRATEGY_SELECTION = "STRATEGY_SELECTION"
    LEARNING_UPDATE = "LEARNING_UPDATE"


class MemoryType(Enum):
    """Types of long-term memory"""
    PATTERN = "PATTERN"
    STRATEGY = "STRATEGY"
    ARCHETYPE = "ARCHETYPE"
    CORRELATION = "CORRELATION"
    THRESHOLD = "THRESHOLD"
    RULE = "RULE"


class SignalType(Enum):
    """Types of signals agents can exchange"""
    WHALE_ACTIVITY = "WHALE_ACTIVITY"
    POSITIVE_NARRATIVE = "POSITIVE_NARRATIVE"
    NEGATIVE_NARRATIVE = "NEGATIVE_NARRATIVE"
    INSTITUTIONAL_ACCUMULATION = "INSTITUTIONAL_ACCUMULATION"
    INSTITUTIONAL_DISTRIBUTION = "INSTITUTIONAL_DISTRIBUTION"
    EXTREME_FUNDING = "EXTREME_FUNDING"
    EXTREME_GREED = "EXTREME_GREED"
    EXTREME_FEAR = "EXTREME_FEAR"
    LIQUIDATION_CASCADE = "LIQUIDATION_CASCADE"
    ARBITRAGE_OPPORTUNITY = "ARBITRAGE_OPPORTUNITY"
    TECHNICAL_BREAKOUT = "TECHNICAL_BREAKOUT"
    RISK_WARNING = "RISK_WARNING"
    TRADE_RECOMMENDATION = "TRADE_RECOMMENDATION"


class SignalSeverity(Enum):
    """Severity levels for signals"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AgentStatus(Enum):
    """Agent operational status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    LEARNING = "learning"
    BACKTEST = "backtest"


class StateType(Enum):
    """Types of agent state"""
    CURRENT = "CURRENT"
    CHECKPOINT = "CHECKPOINT"
    BACKUP = "BACKUP"
    ROLLBACK = "ROLLBACK"


class ProcessingStatus(Enum):
    """Signal processing status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"
    IGNORED = "IGNORED"


# Export all enums
__all__ = [
    'DecisionType',
    'MemoryType',
    'SignalType',
    'SignalSeverity',
    'AgentStatus',
    'StateType',
    'ProcessingStatus',
]
