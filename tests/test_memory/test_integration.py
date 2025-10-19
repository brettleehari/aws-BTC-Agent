"""
Integration test for memory system.

Tests end-to-end flow:
1. Create DynamoDB tables
2. Store and retrieve decisions
3. Store and retrieve patterns
4. Query operations (STM/LTM)
5. State management
6. Signal publishing
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List

from src.memory.memory_manager import MemoryManager
from src.memory.decision_logger import DecisionLogger
from src.memory.models import (
    DecisionRecord, DecisionContext, DecisionReasoning, DecisionOutcome,
    MemoryPattern, AgentState, AgentSignal
)
from src.memory.enums import (
    DecisionType, MemoryType, SignalType, SignalSeverity,
    ProcessingStatus, AgentStatus, StateType
)


class TestMemorySystemIntegration:
    """Integration tests for complete memory system."""
    
    @pytest.fixture
    async def memory_manager(self):
        """Create memory manager instance."""
        return MemoryManager()
    
    @pytest.fixture
    async def decision_logger(self):
        """Create decision logger instance."""
        return DecisionLogger()
    
    @pytest.mark.asyncio
    async def test_decision_lifecycle(self, decision_logger: DecisionLogger):
        """Test complete decision logging lifecycle."""
        
        # 1. Log a decision
        context = DecisionContext(
            market_conditions={"btc_price": 45000, "trend": "bullish"},
            agent_state={"confidence": 0.8},
            available_resources=["coindesk", "twitter"]
        )
        
        reasoning = DecisionReasoning(
            confidence_score=0.85,
            alternative_options=["use_reddit", "use_news_api"],
            risk_assessment={"level": "medium"}
        )
        
        decision_id = await decision_logger.log_decision(
            agent_id="market-hunter-test",
            decision_type=DecisionType.SOURCE_SELECTION,
            decision_made="Selected coindesk for market data",
            context=context,
            reasoning=reasoning
        )
        
        assert decision_id is not None
        print(f"✅ Logged decision: {decision_id}")
        
        # 2. Retrieve the decision
        decision = await decision_logger.get_decision(decision_id)
        assert decision is not None
        assert decision.agent_id == "market-hunter-test"
        assert decision.decision_type == DecisionType.SOURCE_SELECTION
        print(f"✅ Retrieved decision: {decision.decision_id}")
        
        # 3. Update with outcome
        outcome = DecisionOutcome(
            success=True,
            actual_result={"data_quality": 0.9, "latency_ms": 120},
            execution_time_ms=150,
            metrics={"accuracy": 0.92}
        )
        
        await decision_logger.log_outcome(
            decision_id=decision_id,
            outcome=outcome
        )
        
        # 4. Retrieve updated decision
        updated_decision = await decision_logger.get_decision(decision_id)
        assert updated_decision.outcome is not None
        assert updated_decision.outcome.success is True
        print(f"✅ Updated decision with outcome")
        
        # 5. Query recent decisions
        recent = await decision_logger.query_decisions(
            agent_id="market-hunter-test",
            start_time=datetime.now(timezone.utc) - timedelta(minutes=5)
        )
        
        assert len(recent) > 0
        assert any(d.decision_id == decision_id for d in recent)
        print(f"✅ Queried {len(recent)} recent decisions")
    
    @pytest.mark.asyncio
    async def test_pattern_storage_and_retrieval(self, memory_manager: MemoryManager):
        """Test pattern storage and retrieval."""
        
        # 1. Create a pattern
        pattern = MemoryPattern(
            pattern_id=f"pattern-test-{datetime.now(timezone.utc).timestamp()}",
            agent_id="market-hunter-test",
            memory_type=MemoryType.PATTERN,
            name="Bullish divergence",
            description="Price makes lower low while RSI makes higher low",
            data={
                "indicators": ["RSI", "Price"],
                "conditions": ["divergence"],
                "success_rate": 0.78
            },
            confidence=0.82,
            last_updated=datetime.now(timezone.utc),
            version=1
        )
        
        # 2. Store pattern
        await memory_manager.store_pattern(pattern)
        print(f"✅ Stored pattern: {pattern.pattern_id}")
        
        # 3. Retrieve pattern
        retrieved = await memory_manager.get_pattern(pattern.pattern_id)
        assert retrieved is not None
        assert retrieved.name == "Bullish divergence"
        assert retrieved.confidence == 0.82
        print(f"✅ Retrieved pattern: {retrieved.pattern_id}")
        
        # 4. Update confidence
        await memory_manager.update_pattern_confidence(
            pattern_id=pattern.pattern_id,
            new_confidence=0.85
        )
        
        updated = await memory_manager.get_pattern(pattern.pattern_id)
        assert updated.confidence == 0.85
        print(f"✅ Updated pattern confidence to {updated.confidence}")
        
        # 5. Query patterns
        patterns = await memory_manager.query_patterns(
            agent_id="market-hunter-test",
            memory_type=MemoryType.PATTERN,
            min_confidence=0.80
        )
        
        assert len(patterns) > 0
        print(f"✅ Queried {len(patterns)} patterns")
    
    @pytest.mark.asyncio
    async def test_stm_ltm_separation(self, memory_manager: MemoryManager):
        """Test short-term vs long-term memory separation."""
        
        # Create decisions at different times
        now = datetime.now(timezone.utc)
        
        # Recent decision (STM - less than 1 day)
        stm_context = DecisionContext(
            market_conditions={"price": 46000},
            agent_state={},
            available_resources=[]
        )
        
        stm_reasoning = DecisionReasoning(
            confidence_score=0.8,
            alternative_options=[],
            risk_assessment={}
        )
        
        stm_decision = DecisionRecord(
            decision_id=f"stm-{now.timestamp()}",
            agent_id="test-agent",
            decision_type=DecisionType.SIGNAL_GENERATION,
            timestamp=now,
            context=stm_context,
            decision_made="Generate signal",
            reasoning=stm_reasoning
        )
        
        await memory_manager.store_decision(stm_decision)
        
        # Old decision (LTM - more than 1 day)
        ltm_timestamp = now - timedelta(days=2)
        ltm_decision = DecisionRecord(
            decision_id=f"ltm-{ltm_timestamp.timestamp()}",
            agent_id="test-agent",
            decision_type=DecisionType.SIGNAL_GENERATION,
            timestamp=ltm_timestamp,
            context=stm_context,
            decision_made="Old signal",
            reasoning=stm_reasoning
        )
        
        await memory_manager.store_decision(ltm_decision)
        
        # Query STM (last 24 hours)
        stm_results = await memory_manager.query_recent_decisions(
            agent_id="test-agent",
            hours=24
        )
        
        # STM should contain recent decision
        stm_ids = [d.decision_id for d in stm_results]
        assert stm_decision.decision_id in stm_ids
        assert ltm_decision.decision_id not in stm_ids
        print(f"✅ STM query returned {len(stm_results)} recent decisions")
        
        # Query all decisions (including LTM)
        all_results = await memory_manager.query_decisions(
            agent_id="test-agent",
            start_time=now - timedelta(days=3)
        )
        
        all_ids = [d.decision_id for d in all_results]
        assert stm_decision.decision_id in all_ids
        assert ltm_decision.decision_id in all_ids
        print(f"✅ Full query returned {len(all_results)} total decisions")
    
    @pytest.mark.asyncio
    async def test_agent_state_management(self, memory_manager: MemoryManager):
        """Test agent state storage and retrieval."""
        
        # 1. Create agent state
        state = AgentState(
            agent_id="test-agent-state",
            timestamp=datetime.now(timezone.utc),
            state_type=StateType.CURRENT,
            status=AgentStatus.ACTIVE,
            current_cycle=1,
            performance_metrics={"success_rate": 0.85},
            configuration={"update_interval": 300}
        )
        
        # 2. Save state
        await memory_manager.save_state(state)
        print(f"✅ Saved agent state")
        
        # 3. Retrieve state
        retrieved = await memory_manager.get_agent_state("test-agent-state")
        assert retrieved is not None
        assert retrieved.status == AgentStatus.ACTIVE
        assert retrieved.current_cycle == 1
        print(f"✅ Retrieved agent state")
        
        # 4. Update state
        state.current_cycle = 2
        state.status = AgentStatus.IDLE
        await memory_manager.update_agent_state(state)
        
        updated = await memory_manager.get_agent_state("test-agent-state")
        assert updated.current_cycle == 2
        assert updated.status == AgentStatus.IDLE
        print(f"✅ Updated agent state")
    
    @pytest.mark.asyncio
    async def test_signal_publishing_and_retrieval(self, memory_manager: MemoryManager):
        """Test signal publishing and retrieval."""
        
        # 1. Create signal
        signal = AgentSignal(
            signal_id=f"sig-{datetime.now(timezone.utc).timestamp()}",
            source_agent_id="market-hunter-test",
            target_agent_id="risk-manager-test",
            signal_type=SignalType.WHALE_ACTIVITY,
            severity=SignalSeverity.HIGH,
            timestamp=datetime.now(timezone.utc),
            data={
                "wallet": "0xabc123",
                "amount": 1000,
                "action": "large_deposit"
            },
            processing_status=ProcessingStatus.PENDING
        )
        
        # 2. Publish signal
        await memory_manager.publish_signal(signal)
        print(f"✅ Published signal: {signal.signal_id}")
        
        # 3. Retrieve signals for target agent
        signals = await memory_manager.get_signals_for_agent(
            agent_id="risk-manager-test",
            limit=10
        )
        
        assert len(signals) > 0
        signal_ids = [s.signal_id for s in signals]
        assert signal.signal_id in signal_ids
        print(f"✅ Retrieved {len(signals)} signals for target agent")
        
        # 4. Update processing status
        await memory_manager.update_signal_processing_status(
            signal_id=signal.signal_id,
            status=ProcessingStatus.PROCESSED,
            response_data={"action_taken": "risk_assessed"}
        )
        
        # Verify update (would need to add get_signal method to memory_manager)
        print(f"✅ Updated signal processing status")
    
    @pytest.mark.asyncio
    async def test_multi_agent_scenario(self, memory_manager: MemoryManager):
        """Test multi-agent memory operations."""
        
        agents = ["agent-1", "agent-2", "agent-3"]
        
        # Each agent makes decisions
        for agent_id in agents:
            context = DecisionContext(
                market_conditions={"price": 45000 + agents.index(agent_id) * 100},
                agent_state={},
                available_resources=[]
            )
            
            reasoning = DecisionReasoning(
                confidence_score=0.8,
                alternative_options=[],
                risk_assessment={}
            )
            
            decision = DecisionRecord(
                decision_id=f"{agent_id}-decision-{datetime.now(timezone.utc).timestamp()}",
                agent_id=agent_id,
                decision_type=DecisionType.SOURCE_SELECTION,
                timestamp=datetime.now(timezone.utc),
                context=context,
                decision_made=f"{agent_id} made decision",
                reasoning=reasoning
            )
            
            await memory_manager.store_decision(decision)
        
        print(f"✅ Created decisions for {len(agents)} agents")
        
        # Query decisions for each agent
        for agent_id in agents:
            decisions = await memory_manager.query_decisions(
                agent_id=agent_id,
                start_time=datetime.now(timezone.utc) - timedelta(minutes=5)
            )
            
            assert len(decisions) > 0
            # All decisions should belong to this agent
            assert all(d.agent_id == agent_id for d in decisions)
        
        print(f"✅ Verified agent-specific decision queries")


async def run_integration_tests():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("Memory System Integration Tests")
    print("=" * 60)
    
    test_suite = TestMemorySystemIntegration()
    
    # Create fixtures
    memory_manager = MemoryManager()
    decision_logger = DecisionLogger()
    
    tests = [
        ("Decision Lifecycle", test_suite.test_decision_lifecycle(decision_logger)),
        ("Pattern Storage", test_suite.test_pattern_storage_and_retrieval(memory_manager)),
        ("STM/LTM Separation", test_suite.test_stm_ltm_separation(memory_manager)),
        ("Agent State", test_suite.test_agent_state_management(memory_manager)),
        ("Signal Publishing", test_suite.test_signal_publishing_and_retrieval(memory_manager)),
        ("Multi-Agent", test_suite.test_multi_agent_scenario(memory_manager))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_coro in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            await test_coro
            print(f"✅ PASSED: {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == '__main__':
    # Run tests
    asyncio.run(run_integration_tests())
