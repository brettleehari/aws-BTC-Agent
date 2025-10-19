"""
Example: Using the Memory System

Demonstrates how to use the memory system for decision logging and pattern storage.
"""

import logging
from datetime import datetime

# Import memory system components
from src.memory import (
    get_client_manager,
    MemoryManager,
    DecisionLogger,
    DecisionType,
    MemoryType,
    SignalType,
    SignalSeverity,
    AgentStatus,
    StateType,
    MemoryPattern,
    AgentState,
    AgentSignal
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_tables():
    """Create DynamoDB tables (run once)"""
    logger.info("Setting up DynamoDB tables...")
    
    # Get client manager
    # For local testing, use: endpoint_url="http://localhost:8000"
    client_manager = get_client_manager(region="us-east-1")
    
    # Create all tables
    results = client_manager.create_all_tables()
    
    for table_name, created in results.items():
        if created:
            logger.info(f"✓ Created table: {table_name}")
        else:
            logger.info(f"- Table already exists: {table_name}")
    
    logger.info("Table setup complete!")


def example_decision_logging():
    """Example: Logging agent decisions"""
    logger.info("\n=== Example: Decision Logging ===")
    
    # Initialize memory manager for an agent
    memory_manager = MemoryManager(agent_id="btc-agent-001")
    
    # Create decision logger
    decision_logger = DecisionLogger(memory_manager)
    
    # 1. Log a source selection decision
    decision_id = decision_logger.log_source_selection(
        sources=["coinglass", "cryptoquant", "glassnode"],
        scores={
            "coinglass": 0.95,
            "cryptoquant": 0.88,
            "glassnode": 0.82
        },
        selected=["coinglass", "cryptoquant"],
        context={
            "market": {
                "btc_price": 45000.00,
                "volatility": 0.035,
                "trend": "bullish"
            },
            "cycle": 1,
            "trading_hours": True
        },
        confidence=0.92
    )
    
    logger.info(f"✓ Logged source selection decision: {decision_id}")
    
    # 2. Log the outcome after execution
    decision_logger.log_outcome(
        decision_id=decision_id,
        decision_type=DecisionType.SOURCE_SELECTION,
        success=True,
        quality_score=0.89,
        latency_ms=250.5,
        metrics={
            "sources_queried": 2,
            "data_freshness": 0.95
        }
    )
    
    logger.info(f"✓ Logged outcome for decision: {decision_id}")
    
    # 3. Log a child decision (query execution)
    query_decision_id = decision_logger.log_query_execution(
        query="Get BTC funding rates for last 24h",
        sources=["coinglass", "cryptoquant"],
        context={
            "market": {"btc_price": 45000.00},
            "cycle": 1
        },
        parent_decision_id=decision_id  # Link to parent
    )
    
    logger.info(f"✓ Logged query execution decision: {query_decision_id}")
    
    # 4. Get recent decisions
    recent = decision_logger.get_recent_decisions(limit=10)
    logger.info(f"✓ Retrieved {len(recent)} recent decisions")
    
    # 5. Get decision statistics
    stats = decision_logger.get_decision_stats(time_window_hours=24)
    logger.info(f"✓ Decision stats: {stats['count']} decisions, "
                f"{stats['success_rate']:.2%} success rate, "
                f"{stats['avg_confidence']:.2f} avg confidence")


def example_pattern_storage():
    """Example: Storing and retrieving patterns (LTM)"""
    logger.info("\n=== Example: Pattern Storage ===")
    
    # Initialize memory manager
    memory_manager = MemoryManager(agent_id="btc-agent-001")
    
    # 1. Create a pattern
    pattern = MemoryPattern(
        agent_id="btc-agent-001",
        memory_type=MemoryType.PATTERN,
        confidence=0.85,
        success_rate=0.78,
        sample_size=120,
        data={
            "pattern_name": "High Funding + Whale Accumulation",
            "conditions": {
                "funding_rate": "> 0.15%",
                "whale_net_flow": "positive",
                "timeframe": "4h"
            },
            "expected_outcome": "Price increase within 24h",
            "risk_level": "medium"
        },
        user_metadata={
            # TO BE POPULATED BY USER
            # Add your custom pattern details here
            "custom_field_1": "value1",
            "custom_field_2": "value2"
        }
    )
    
    # Store the pattern
    if memory_manager.store_pattern(pattern):
        logger.info(f"✓ Stored pattern: {pattern.pattern_id}")
    
    # 2. Query patterns by type
    patterns = memory_manager.query_patterns(
        memory_type=MemoryType.PATTERN,
        min_confidence=0.70,
        limit=10
    )
    
    logger.info(f"✓ Retrieved {len(patterns)} patterns with confidence >= 0.70")
    
    # 3. Update pattern metrics after usage
    memory_manager.update_pattern_metrics(
        pattern_id=pattern.pattern_id,
        memory_type=MemoryType.PATTERN,
        success=True,
        new_confidence=0.87
    )
    
    logger.info(f"✓ Updated pattern metrics")


def example_state_management():
    """Example: Saving and loading agent state"""
    logger.info("\n=== Example: State Management ===")
    
    # Initialize memory manager
    memory_manager = MemoryManager(agent_id="btc-agent-001")
    
    # 1. Create agent state
    state = AgentState(
        agent_id="btc-agent-001",
        agent_version="1.0.0",
        state_type=StateType.CURRENT,
        status=AgentStatus.ACTIVE,
        current_cycle=42,
        source_metrics={
            "coinglass": {"quality": 0.95, "latency": 150},
            "cryptoquant": {"quality": 0.88, "latency": 200}
        },
        context_performance={
            "decision_accuracy": 0.82,
            "signal_precision": 0.76
        },
        configuration={
            "risk_tolerance": 0.5,
            "exploration_rate": 0.1,
            "learning_enabled": True
        }
    )
    
    # Save state
    if memory_manager.save_state(state):
        logger.info(f"✓ Saved agent state (cycle {state.current_cycle})")
    
    # 2. Create a checkpoint
    if memory_manager.checkpoint_state():
        logger.info(f"✓ Created state checkpoint")
    
    # 3. Load state
    loaded_state = memory_manager.load_state(StateType.CURRENT)
    if loaded_state:
        logger.info(f"✓ Loaded state: cycle {loaded_state.current_cycle}, "
                    f"status {loaded_state.status.value}")


def example_signal_publishing():
    """Example: Publishing and consuming signals (multi-agent)"""
    logger.info("\n=== Example: Signal Publishing ===")
    
    # Initialize memory managers for two agents
    agent1_memory = MemoryManager(agent_id="btc-agent-001")
    agent2_memory = MemoryManager(agent_id="btc-agent-002")
    
    # 1. Agent 1 publishes a signal
    signal = AgentSignal(
        signal_type=SignalType.WHALE_ACTIVITY,
        source_agent="btc-agent-001",
        target_agents=["btc-agent-002", "btc-agent-003"],
        severity=SignalSeverity.HIGH,
        confidence=0.92,
        data={
            "whale_address": "bc1q...",
            "transfer_amount_btc": 1500.0,
            "transfer_usd": 67500000.0,
            "direction": "exchange_to_cold_wallet"
        },
        context={
            "btc_price": 45000.0,
            "time": datetime.utcnow().isoformat()
        },
        recommended_action="Monitor for potential accumulation phase"
    )
    
    if agent1_memory.publish_signal(signal):
        logger.info(f"✓ Agent 1 published signal: {signal.signal_id}")
    
    # 2. Agent 2 retrieves pending signals
    pending_signals = agent2_memory.get_pending_signals(limit=10)
    logger.info(f"✓ Agent 2 has {len(pending_signals)} pending signals")
    
    # 3. Agent 2 processes the signal
    if pending_signals:
        signal_to_process = pending_signals[0]
        logger.info(f"✓ Agent 2 processing signal: {signal_to_process.signal_type.value}")
        
        # Mark as processed
        agent2_memory.mark_signal_processed(
            signal_id=signal_to_process.signal_id,
            signal_type=signal_to_process.signal_type,
            status='PROCESSED'
        )
        
        logger.info(f"✓ Agent 2 marked signal as processed")


def example_cleanup():
    """Example: Cleanup old short-term memory"""
    logger.info("\n=== Example: Cleanup ===")
    
    # Initialize memory manager
    memory_manager = MemoryManager(agent_id="btc-agent-001")
    
    # Clean up STM older than 24 hours
    deleted_count = memory_manager.cleanup_stm(older_than_hours=24)
    logger.info(f"✓ Cleaned up {deleted_count} old STM decisions")


def main():
    """Run all examples"""
    logger.info("=" * 60)
    logger.info("Memory System Examples")
    logger.info("=" * 60)
    
    # Note: Uncomment this to create tables (run once)
    # setup_tables()
    
    # Run examples (requires tables to exist)
    try:
        example_decision_logging()
        example_pattern_storage()
        example_state_management()
        example_signal_publishing()
        example_cleanup()
        
        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
