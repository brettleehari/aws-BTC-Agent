"""
Agent Memory and Decision Logging System

Provides hierarchical memory (STM/LTM), decision logging, and multi-agent coordination.
"""

from .enums import (
    DecisionType,
    MemoryType,
    SignalType,
    SignalSeverity,
    AgentStatus,
    StateType,
    ProcessingStatus
)

from .models import (
    DecisionRecord,
    DecisionContext,
    DecisionReasoning,
    DecisionOutcome,
    MemoryPattern,
    AgentState,
    AgentSignal
)

from .aws_clients import AWSClientManager, get_client_manager

from .memory_manager import MemoryManager

from .decision_logger import DecisionLogger


__version__ = "1.0.0"

__all__ = [
    # Enums
    'DecisionType',
    'MemoryType',
    'SignalType',
    'SignalSeverity',
    'AgentStatus',
    'StateType',
    'ProcessingStatus',
    
    # Models
    'DecisionRecord',
    'DecisionContext',
    'DecisionReasoning',
    'DecisionOutcome',
    'MemoryPattern',
    'AgentState',
    'AgentSignal',
    
    # AWS Clients
    'AWSClientManager',
    'get_client_manager',
    
    # Core Managers
    'MemoryManager',
    'DecisionLogger',
]
