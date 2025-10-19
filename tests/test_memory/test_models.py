"""
Basic unit tests for memory system models.

Tests Pydantic model validation and DynamoDB conversion.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from src.memory.models import (
    DecisionRecord, DecisionContext, DecisionReasoning, DecisionOutcome,
    MemoryPattern, AgentState, AgentSignal
)
from src.memory.enums import (
    DecisionType, MemoryType, SignalType, SignalSeverity,
    ProcessingStatus, AgentStatus, StateType
)


class TestDecisionRecord:
    """Test DecisionRecord model."""
    
    def test_decision_record_creation(self):
        """Test creating a decision record."""
        context = DecisionContext(
            market_conditions={"btc_price": 45000, "trend": "bullish"},
            agent_state={"confidence": 0.8},
            available_resources=["source1", "source2"]
        )
        
        reasoning = DecisionReasoning(
            confidence_score=0.85,
            alternative_options=["option1", "option2"],
            risk_assessment={"level": "medium"}
        )
        
        record = DecisionRecord(
            decision_id="test-123",
            agent_id="market-hunter",
            decision_type=DecisionType.SOURCE_SELECTION,
            timestamp=datetime.now(timezone.utc),
            context=context,
            decision_made="Selected source1",
            reasoning=reasoning
        )
        
        assert record.decision_id == "test-123"
        assert record.agent_id == "market-hunter"
        assert record.decision_type == DecisionType.SOURCE_SELECTION
        assert record.context.market_conditions["btc_price"] == 45000
        assert record.reasoning.confidence_score == 0.85
    
    def test_decision_with_outcome(self):
        """Test decision record with outcome."""
        context = DecisionContext(
            market_conditions={},
            agent_state={},
            available_resources=[]
        )
        
        reasoning = DecisionReasoning(
            confidence_score=0.9,
            alternative_options=[],
            risk_assessment={}
        )
        
        outcome = DecisionOutcome(
            success=True,
            actual_result={"profit": 100},
            execution_time_ms=150,
            metrics={"accuracy": 0.95}
        )
        
        record = DecisionRecord(
            decision_id="test-456",
            agent_id="risk-manager",
            decision_type=DecisionType.RISK_ASSESSMENT,
            timestamp=datetime.now(timezone.utc),
            context=context,
            decision_made="Risk approved",
            reasoning=reasoning,
            outcome=outcome
        )
        
        assert record.outcome is not None
        assert record.outcome.success is True
        assert record.outcome.metrics["accuracy"] == 0.95
    
    def test_decision_dynamodb_conversion(self):
        """Test conversion to/from DynamoDB format."""
        context = DecisionContext(
            market_conditions={"price": 50000},
            agent_state={"status": "active"},
            available_resources=["res1"]
        )
        
        reasoning = DecisionReasoning(
            confidence_score=0.75,
            alternative_options=["alt1"],
            risk_assessment={"level": "low"}
        )
        
        original = DecisionRecord(
            decision_id="test-789",
            agent_id="trader",
            decision_type=DecisionType.TRADE_EXECUTION,
            timestamp=datetime.now(timezone.utc),
            context=context,
            decision_made="Execute trade",
            reasoning=reasoning
        )
        
        # Convert to DynamoDB
        dynamo_item = original.to_dynamodb_item()
        
        # Check DynamoDB format
        assert dynamo_item['decision_id'] == "test-789"
        assert dynamo_item['agent_id'] == "trader"
        assert dynamo_item['decision_type'] == "TRADE_EXECUTION"
        assert isinstance(dynamo_item['timestamp'], str)
        
        # Convert back from DynamoDB
        restored = DecisionRecord.from_dynamodb_item(dynamo_item)
        
        # Verify restoration
        assert restored.decision_id == original.decision_id
        assert restored.agent_id == original.agent_id
        assert restored.decision_type == original.decision_type
        assert restored.decision_made == original.decision_made


class TestMemoryPattern:
    """Test MemoryPattern model."""
    
    def test_pattern_creation(self):
        """Test creating a memory pattern."""
        pattern = MemoryPattern(
            pattern_id="pattern-001",
            agent_id="market-hunter",
            memory_type=MemoryType.PATTERN,
            name="Bullish divergence pattern",
            description="Price makes lower low while RSI makes higher low",
            data={
                "indicators": ["RSI", "Price"],
                "conditions": ["divergence"],
                "threshold": 30
            },
            confidence=0.82,
            last_updated=datetime.now(timezone.utc),
            version=1
        )
        
        assert pattern.pattern_id == "pattern-001"
        assert pattern.memory_type == MemoryType.PATTERN
        assert pattern.confidence == 0.82
        assert pattern.data["threshold"] == 30
    
    def test_pattern_metadata(self):
        """Test pattern with metadata."""
        pattern = MemoryPattern(
            pattern_id="pattern-002",
            agent_id="signal-processor",
            memory_type=MemoryType.STRATEGY,
            name="Conservative strategy",
            description="Low risk trading strategy",
            data={"risk_level": "low"},
            confidence=0.90,
            last_updated=datetime.now(timezone.utc),
            version=2,
            metadata={
                "creator": "system",
                "validated": True,
                "success_count": 42
            }
        )
        
        assert pattern.metadata["success_count"] == 42
        assert pattern.metadata["validated"] is True
    
    def test_pattern_dynamodb_conversion(self):
        """Test pattern DynamoDB conversion."""
        original = MemoryPattern(
            pattern_id="pattern-003",
            agent_id="analyst",
            memory_type=MemoryType.ARCHETYPE,
            name="Market cycle archetype",
            description="Bull/bear cycle pattern",
            data={"phases": ["accumulation", "markup", "distribution", "markdown"]},
            confidence=0.88,
            last_updated=datetime.now(timezone.utc),
            version=1
        )
        
        # Convert to DynamoDB
        dynamo_item = original.to_dynamodb_item()
        
        # Check conversions
        assert isinstance(dynamo_item['confidence'], Decimal)
        assert float(dynamo_item['confidence']) == 0.88
        assert dynamo_item['memory_type'] == "ARCHETYPE"
        
        # Convert back
        restored = MemoryPattern.from_dynamodb_item(dynamo_item)
        
        assert restored.pattern_id == original.pattern_id
        assert restored.confidence == original.confidence
        assert restored.data["phases"] == original.data["phases"]


class TestAgentState:
    """Test AgentState model."""
    
    def test_agent_state_creation(self):
        """Test creating agent state."""
        state = AgentState(
            agent_id="market-hunter",
            timestamp=datetime.now(timezone.utc),
            state_type=StateType.CURRENT,
            status=AgentStatus.ACTIVE,
            current_cycle=5,
            last_decision_id="dec-123",
            performance_metrics={
                "success_rate": 0.85,
                "total_decisions": 100
            },
            configuration={
                "update_interval": 300,
                "risk_tolerance": "medium"
            }
        )
        
        assert state.agent_id == "market-hunter"
        assert state.status == AgentStatus.ACTIVE
        assert state.current_cycle == 5
        assert state.performance_metrics["success_rate"] == 0.85
    
    def test_agent_state_dynamodb_conversion(self):
        """Test agent state DynamoDB conversion."""
        original = AgentState(
            agent_id="trader-bot",
            timestamp=datetime.now(timezone.utc),
            state_type=StateType.CHECKPOINT,
            status=AgentStatus.IDLE,
            current_cycle=10,
            performance_metrics={"trades": 50},
            configuration={"mode": "conservative"}
        )
        
        # Convert
        dynamo_item = original.to_dynamodb_item()
        
        assert dynamo_item['agent_id'] == "trader-bot"
        assert dynamo_item['status'] == "IDLE"
        assert dynamo_item['state_type'] == "CHECKPOINT"
        
        # Restore
        restored = AgentState.from_dynamodb_item(dynamo_item)
        
        assert restored.agent_id == original.agent_id
        assert restored.status == original.status
        assert restored.current_cycle == original.current_cycle


class TestAgentSignal:
    """Test AgentSignal model."""
    
    def test_signal_creation(self):
        """Test creating an agent signal."""
        signal = AgentSignal(
            signal_id="sig-001",
            source_agent_id="market-hunter",
            target_agent_id="risk-manager",
            signal_type=SignalType.WHALE_ACTIVITY,
            severity=SignalSeverity.HIGH,
            timestamp=datetime.now(timezone.utc),
            data={
                "wallet": "0x123...",
                "amount": 1000,
                "action": "deposit"
            },
            processing_status=ProcessingStatus.PENDING
        )
        
        assert signal.signal_type == SignalType.WHALE_ACTIVITY
        assert signal.severity == SignalSeverity.HIGH
        assert signal.processing_status == ProcessingStatus.PENDING
        assert signal.data["amount"] == 1000
    
    def test_signal_with_response(self):
        """Test signal with response."""
        signal = AgentSignal(
            signal_id="sig-002",
            source_agent_id="sentiment-analyzer",
            target_agent_id="trader",
            signal_type=SignalType.POSITIVE_NARRATIVE,
            severity=SignalSeverity.MEDIUM,
            timestamp=datetime.now(timezone.utc),
            data={"sentiment_score": 0.75},
            processing_status=ProcessingStatus.PROCESSED,
            processed_at=datetime.now(timezone.utc),
            response_data={"action_taken": "increased_position"}
        )
        
        assert signal.processing_status == ProcessingStatus.PROCESSED
        assert signal.response_data["action_taken"] == "increased_position"
    
    def test_signal_dynamodb_conversion(self):
        """Test signal DynamoDB conversion."""
        original = AgentSignal(
            signal_id="sig-003",
            source_agent_id="detector",
            target_agent_id="executor",
            signal_type=SignalType.REGULATORY_CHANGE,
            severity=SignalSeverity.CRITICAL,
            timestamp=datetime.now(timezone.utc),
            data={"regulation": "new_law"},
            processing_status=ProcessingStatus.PENDING
        )
        
        # Convert
        dynamo_item = original.to_dynamodb_item()
        
        assert dynamo_item['signal_type'] == "REGULATORY_CHANGE"
        assert dynamo_item['severity'] == "CRITICAL"
        
        # Restore
        restored = AgentSignal.from_dynamodb_item(dynamo_item)
        
        assert restored.signal_id == original.signal_id
        assert restored.signal_type == original.signal_type
        assert restored.severity == original.severity


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
