"""
Pydantic Models for Agent Memory System

Defines all data models with validation for memory, decisions, signals, and agent state.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from uuid import uuid4

from .enums import (
    DecisionType,
    MemoryType,
    SignalType,
    SignalSeverity,
    AgentStatus,
    StateType,
    ProcessingStatus
)


class DecisionContext(BaseModel):
    """Context information when a decision was made"""
    market: Dict[str, Any] = Field(default_factory=dict, description="Market conditions")
    cycle: Optional[int] = Field(None, description="Agent cycle number")
    trading_hours: Optional[str] = Field(None, description="Trading hours region")
    parent_decision_id: Optional[str] = Field(None, description="Parent decision if chained")
    agent_state: Dict[str, Any] = Field(default_factory=dict, description="Agent state snapshot")
    
    class Config:
        extra = "allow"  # Allow additional fields


class DecisionReasoning(BaseModel):
    """Reasoning behind a decision"""
    scores: Dict[str, float] = Field(default_factory=dict, description="Calculated scores")
    selected: List[str] = Field(default_factory=list, description="Selected items")
    memory_influenced: bool = Field(False, description="Was memory used in decision")
    patterns_applied: List[str] = Field(default_factory=list, description="Pattern IDs applied")
    exploration: bool = Field(False, description="Was this an exploration decision")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Decision confidence")
    
    class Config:
        extra = "allow"


class DecisionOutcome(BaseModel):
    """Outcome of a decision"""
    success: bool = Field(..., description="Whether decision was successful")
    signals_generated: int = Field(0, ge=0, description="Number of signals generated")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Outcome quality")
    latency_ms: Optional[int] = Field(None, ge=0, description="Decision execution latency")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Additional metrics")
    
    class Config:
        extra = "allow"


class DecisionRecord(BaseModel):
    """Complete decision record"""
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid4().hex[:12]}", description="Unique decision ID")
    agent_id: str = Field(..., description="Agent that made the decision")
    agent_version: str = Field(default="1.0.0", description="Agent version")
    decision_type: DecisionType = Field(..., description="Type of decision")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When decision was made")
    
    context: DecisionContext = Field(default_factory=DecisionContext, description="Decision context")
    reasoning: DecisionReasoning = Field(default_factory=DecisionReasoning, description="Decision reasoning")
    outcome: Optional[DecisionOutcome] = Field(None, description="Decision outcome (filled later)")
    
    ttl: Optional[int] = Field(None, description="TTL for DynamoDB (Unix timestamp)")
    is_stm: bool = Field(True, description="Is this short-term memory (< 1 day)")
    
    class Config:
        use_enum_values = True
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        iso_timestamp = self.timestamp.isoformat()
        
        item = {
            'PK': f"agent:{self.agent_id}#decision#{self.decision_type.value}",
            'SK': f"{iso_timestamp}#{self.decision_id}",
            'agent_id': self.agent_id,
            'agent_version': self.agent_version,
            'decision_id': self.decision_id,
            'decision_type': self.decision_type.value,
            'timestamp': int(self.timestamp.timestamp()),
            'iso_timestamp': iso_timestamp,
            'context': self.context.dict(),
            'reasoning': self.reasoning.dict(),
            'is_stm': self.is_stm,
        }
        
        if self.outcome:
            item['outcome'] = self.outcome.dict()
        
        if self.ttl:
            item['ttl'] = self.ttl
        
        # GSI keys
        if self.outcome:
            item['GSI1_PK'] = f"agent:{self.agent_id}#{'success' if self.outcome.success else 'failure'}"
            item['GSI1_SK'] = int(self.timestamp.timestamp())
        
        item['GSI2_PK'] = f"decision_type#{self.decision_type.value}"
        item['GSI2_SK'] = int(self.timestamp.timestamp())
        
        item['GSI3_PK'] = f"agent:{self.agent_id}#stm" if self.is_stm else f"agent:{self.agent_id}#ltm"
        item['GSI3_SK'] = int(self.timestamp.timestamp())
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'DecisionRecord':
        """Create from DynamoDB item"""
        return cls(
            decision_id=item['decision_id'],
            agent_id=item['agent_id'],
            agent_version=item.get('agent_version', '1.0.0'),
            decision_type=DecisionType(item['decision_type']),
            timestamp=datetime.fromtimestamp(item['timestamp']),
            context=DecisionContext(**item['context']),
            reasoning=DecisionReasoning(**item['reasoning']),
            outcome=DecisionOutcome(**item['outcome']) if 'outcome' in item else None,
            ttl=item.get('ttl'),
            is_stm=item.get('is_stm', True)
        )


class MemoryPattern(BaseModel):
    """Long-term memory pattern"""
    pattern_id: str = Field(default_factory=lambda: f"pattern_{uuid4().hex[:12]}", description="Unique pattern ID")
    agent_id: str = Field(..., description="Agent that learned the pattern")
    memory_type: MemoryType = Field(..., description="Type of memory")
    
    learned_at: datetime = Field(default_factory=datetime.utcnow, description="When pattern was learned")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    access_count: int = Field(0, ge=0, description="Number of times accessed")
    
    confidence: float = Field(..., ge=0.0, le=1.0, description="Pattern confidence")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Historical success rate")
    sample_size: int = Field(..., ge=0, description="Number of observations")
    
    data: Dict[str, Any] = Field(..., description="Pattern data")
    version: int = Field(1, ge=1, description="Pattern version")
    
    is_shared: bool = Field(False, description="Is this pattern shared across agents")
    shared_with: List[str] = Field(default_factory=list, description="Agent IDs pattern is shared with")
    
    # Placeholder for user-defined pattern details
    user_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-defined pattern metadata - TO BE POPULATED BY USER"
    )
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        item = {
            'PK': f"agent:{self.agent_id}#{self.memory_type.value.lower()}",
            'SK': self.pattern_id,
            'agent_id': self.agent_id,
            'memory_type': self.memory_type.value,
            'pattern_id': self.pattern_id,
            'learned_at': int(self.learned_at.timestamp()),
            'last_accessed': int(self.last_accessed.timestamp()),
            'access_count': self.access_count,
            'confidence': self.confidence,
            'success_rate': self.success_rate,
            'sample_size': self.sample_size,
            'data': self.data,
            'version': self.version,
            'is_shared': self.is_shared,
            'shared_with': self.shared_with,
            'user_metadata': self.user_metadata,
        }
        
        # GSI keys
        item['GSI1_PK'] = f"agent:{self.agent_id}#{self.memory_type.value.lower()}"
        item['GSI1_SK'] = self.confidence  # Sort by confidence (high to low)
        
        if self.is_shared:
            item['GSI2_PK'] = f"shared_pattern#{self.memory_type.value.lower()}"
            item['GSI2_SK'] = self.confidence
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'MemoryPattern':
        """Create from DynamoDB item"""
        return cls(
            pattern_id=item['pattern_id'],
            agent_id=item['agent_id'],
            memory_type=MemoryType(item['memory_type']),
            learned_at=datetime.fromtimestamp(item['learned_at']),
            last_accessed=datetime.fromtimestamp(item['last_accessed']),
            access_count=item['access_count'],
            confidence=item['confidence'],
            success_rate=item['success_rate'],
            sample_size=item['sample_size'],
            data=item['data'],
            version=item['version'],
            is_shared=item.get('is_shared', False),
            shared_with=item.get('shared_with', []),
            user_metadata=item.get('user_metadata', {})
        )


class AgentState(BaseModel):
    """Current agent state"""
    agent_id: str = Field(..., description="Agent identifier")
    agent_version: str = Field(default="1.0.0", description="Agent version")
    state_type: StateType = Field(default=StateType.CURRENT, description="State type")
    status: AgentStatus = Field(default=AgentStatus.ACTIVE, description="Agent status")
    
    current_cycle: int = Field(0, ge=0, description="Current cycle number")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    
    source_metrics: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Source performance metrics")
    context_performance: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Performance by context")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Agent configuration")
    
    version: int = Field(1, ge=1, description="State version number")
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        return {
            'PK': f"agent:{self.agent_id}",
            'SK': self.state_type.value,
            'agent_id': self.agent_id,
            'agent_version': self.agent_version,
            'state_type': self.state_type.value,
            'status': self.status.value,
            'current_cycle': self.current_cycle,
            'last_updated': int(self.last_updated.timestamp()),
            'source_metrics': self.source_metrics,
            'context_performance': self.context_performance,
            'configuration': self.configuration,
            'version': self.version
        }
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'AgentState':
        """Create from DynamoDB item"""
        return cls(
            agent_id=item['agent_id'],
            agent_version=item.get('agent_version', '1.0.0'),
            state_type=StateType(item['state_type']),
            status=AgentStatus(item.get('status', 'active')),
            current_cycle=item['current_cycle'],
            last_updated=datetime.fromtimestamp(item['last_updated']),
            source_metrics=item['source_metrics'],
            context_performance=item['context_performance'],
            configuration=item['configuration'],
            version=item['version']
        )


class AgentSignal(BaseModel):
    """Signal for cross-agent communication"""
    signal_id: str = Field(default_factory=lambda: f"sig_{uuid4().hex[:12]}", description="Unique signal ID")
    signal_type: SignalType = Field(..., description="Type of signal")
    source_agent: str = Field(..., description="Agent that generated the signal")
    target_agents: List[str] = Field(..., description="Target agent IDs")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal generation time")
    severity: SignalSeverity = Field(default=SignalSeverity.MEDIUM, description="Signal severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence")
    
    data: Dict[str, Any] = Field(..., description="Signal data")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context when signal generated")
    recommended_action: Optional[str] = Field(None, description="Recommended action")
    
    processing_status: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Processing status by each target agent"
    )
    
    ttl: Optional[int] = Field(None, description="TTL (Unix timestamp) - signals expire after 24h")
    
    class Config:
        use_enum_values = True
    
    def to_dynamodb_item(self) -> Dict[str, Any]:
        """Convert to DynamoDB item format"""
        iso_timestamp = self.timestamp.isoformat()
        
        item = {
            'PK': f"signal#{self.signal_type.value}",
            'SK': f"{iso_timestamp}#{self.signal_id}",
            'signal_id': self.signal_id,
            'signal_type': self.signal_type.value,
            'source_agent': self.source_agent,
            'target_agents': self.target_agents,
            'timestamp': int(self.timestamp.timestamp()),
            'iso_timestamp': iso_timestamp,
            'severity': self.severity.value,
            'confidence': self.confidence,
            'data': self.data,
            'context': self.context,
            'processing_status': self.processing_status,
        }
        
        if self.recommended_action:
            item['recommended_action'] = self.recommended_action
        
        if self.ttl:
            item['ttl'] = self.ttl
        
        # GSI for querying by target agent
        for target in self.target_agents:
            item[f'GSI1_PK'] = f"target_agent:{target}"
            item[f'GSI1_SK'] = int(self.timestamp.timestamp())
            break  # DynamoDB GSI only supports one value per attribute
        
        return item
    
    @classmethod
    def from_dynamodb_item(cls, item: Dict[str, Any]) -> 'AgentSignal':
        """Create from DynamoDB item"""
        return cls(
            signal_id=item['signal_id'],
            signal_type=SignalType(item['signal_type']),
            source_agent=item['source_agent'],
            target_agents=item['target_agents'],
            timestamp=datetime.fromtimestamp(item['timestamp']),
            severity=SignalSeverity(item['severity']),
            confidence=item['confidence'],
            data=item['data'],
            context=item['context'],
            recommended_action=item.get('recommended_action'),
            processing_status=item['processing_status'],
            ttl=item.get('ttl')
        )


# Export all models
__all__ = [
    'DecisionContext',
    'DecisionReasoning',
    'DecisionOutcome',
    'DecisionRecord',
    'MemoryPattern',
    'AgentState',
    'AgentSignal',
]
