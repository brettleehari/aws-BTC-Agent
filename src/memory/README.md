# Agent Memory and Decision Logging System

A comprehensive memory system for autonomous agents with hierarchical memory (STM/LTM), decision logging, and multi-agent coordination using AWS DynamoDB.

## 🎯 Features

- **Hierarchical Memory**: Short-term (<1 day) and long-term (>1 day) memory separation
- **Decision Logging**: Complete traceability of all agent decisions with context, reasoning, and outcomes
- **Pattern Learning**: Store and retrieve learned patterns with confidence scores and success rates
- **Multi-Agent Support**: Built-in support for multiple agents with shared memory and signal communication
- **State Persistence**: Save and restore agent state across restarts
- **Signal System**: Cross-agent communication for collaborative decision-making
- **AWS Native**: Uses DynamoDB with GSIs for efficient querying
- **Cost Optimized**: ~$3.50/month for demo workloads

## 📁 Directory Structure

```
src/memory/
├── __init__.py              # Package initialization
├── enums.py                 # Type-safe enumerations
├── models.py                # Pydantic data models
├── aws_clients.py           # DynamoDB client management
├── memory_manager.py        # Core CRUD operations
└── decision_logger.py       # High-level decision logging API

examples/
└── memory_system_demo.py    # Complete usage examples

tests/test_memory/           # Unit tests (TODO)

docs/memory/                 # Comprehensive documentation
├── IMPLEMENTATION_PLAN.md   # Architecture details
├── QUICKSTART.md           # Quick reference
└── ...
```

## 🚀 Quick Start

### 1. Setup DynamoDB Tables

```python
from src.memory import get_client_manager

# Create all required tables (run once)
client_manager = get_client_manager(region="us-east-1")
results = client_manager.create_all_tables()

# Tables created:
# - agent_decisions (with 3 GSIs)
# - agent_memory_ltm (with 2 GSIs)
# - agent_state
# - agent_signals (with 1 GSI)
```

### 2. Initialize Memory Manager

```python
from src.memory import MemoryManager, DecisionLogger

# Create memory manager for your agent
memory_manager = MemoryManager(agent_id="btc-agent-001")

# Create decision logger
decision_logger = DecisionLogger(memory_manager)
```

### 3. Log Decisions

```python
from src.memory import DecisionType

# Log a decision
decision_id = decision_logger.log_source_selection(
    sources=["coinglass", "cryptoquant", "glassnode"],
    scores={"coinglass": 0.95, "cryptoquant": 0.88, "glassnode": 0.82},
    selected=["coinglass", "cryptoquant"],
    context={
        "market": {"btc_price": 45000.00, "volatility": 0.035},
        "cycle": 1,
        "trading_hours": True
    },
    confidence=0.92
)

# Log the outcome
decision_logger.log_outcome(
    decision_id=decision_id,
    decision_type=DecisionType.SOURCE_SELECTION,
    success=True,
    quality_score=0.89,
    latency_ms=250.5
)
```

### 4. Store Patterns (Long-Term Memory)

```python
from src.memory import MemoryPattern, MemoryType

# Create a pattern
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
            "whale_net_flow": "positive"
        },
        "expected_outcome": "Price increase within 24h"
    },
    user_metadata={
        # TO BE POPULATED BY USER
        "custom_field": "your_value"
    }
)

# Store the pattern
memory_manager.store_pattern(pattern)

# Query patterns
patterns = memory_manager.query_patterns(
    memory_type=MemoryType.PATTERN,
    min_confidence=0.70
)
```

### 5. Save Agent State

```python
from src.memory import AgentState, AgentStatus, StateType

# Create state
state = AgentState(
    agent_id="btc-agent-001",
    agent_version="1.0.0",
    state_type=StateType.CURRENT,
    status=AgentStatus.ACTIVE,
    current_cycle=42,
    source_metrics={"coinglass": {"quality": 0.95}},
    configuration={"risk_tolerance": 0.5}
)

# Save state
memory_manager.save_state(state)

# Load state
loaded_state = memory_manager.load_state(StateType.CURRENT)
```

### 6. Multi-Agent Signals

```python
from src.memory import AgentSignal, SignalType, SignalSeverity

# Agent 1 publishes a signal
signal = AgentSignal(
    signal_type=SignalType.WHALE_ACTIVITY,
    source_agent="btc-agent-001",
    target_agents=["btc-agent-002", "btc-agent-003"],
    severity=SignalSeverity.HIGH,
    confidence=0.92,
    data={"whale_address": "bc1q...", "amount_btc": 1500.0}
)

agent1_memory.publish_signal(signal)

# Agent 2 retrieves pending signals
pending = agent2_memory.get_pending_signals()

# Agent 2 marks signal as processed
agent2_memory.mark_signal_processed(
    signal_id=signal.signal_id,
    signal_type=signal.signal_type,
    status='PROCESSED'
)
```

## 📊 Data Models

### DecisionRecord
Complete decision logging with context, reasoning, and outcome.

**Key Fields:**
- `decision_id`: Auto-generated unique ID
- `agent_id`: Agent identifier
- `decision_type`: Type of decision (SOURCE_SELECTION, QUERY_EXECUTION, etc.)
- `timestamp`: When decision was made
- `context`: Market conditions, cycle info, parent decision
- `reasoning`: Scores, selections, patterns applied, confidence
- `outcome`: Success flag, quality score, latency, errors
- `is_stm`: Short-term (True) or long-term (False) memory

### MemoryPattern
Long-term learned patterns with confidence tracking.

**Key Fields:**
- `pattern_id`: Auto-generated unique ID
- `agent_id`: Agent identifier
- `memory_type`: Type of pattern (PATTERN, STRATEGY, ARCHETYPE, etc.)
- `confidence`: Pattern confidence (0.0-1.0)
- `success_rate`: Historical success rate (0.0-1.0)
- `sample_size`: Number of observations
- `data`: Pattern details (flexible dict)
- `user_metadata`: **TO BE POPULATED BY USER** - Custom pattern fields
- `is_shared`: Whether pattern is shared with other agents
- `shared_with`: List of agent IDs with access

### AgentState
Current agent state for persistence across restarts.

**Key Fields:**
- `agent_id`: Agent identifier
- `status`: Current status (ACTIVE, PAUSED, ERROR, etc.)
- `current_cycle`: Current execution cycle
- `source_metrics`: Performance metrics per source
- `context_performance`: Decision accuracy, signal precision
- `configuration`: Agent configuration settings

### AgentSignal
Cross-agent communication for multi-agent collaboration.

**Key Fields:**
- `signal_id`: Auto-generated unique ID
- `signal_type`: Type of signal (WHALE_ACTIVITY, EXTREME_FUNDING, etc.)
- `source_agent`: Agent that generated the signal
- `target_agents`: List of agents to receive signal
- `severity`: Signal severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `confidence`: Signal confidence (0.0-1.0)
- `data`: Signal data (flexible dict)
- `processing_status`: Per-agent processing status

## 🔧 Architecture

### DynamoDB Tables

**agent_decisions**
- Stores all decision records
- PK: `agent:{agent_id}#decision#{type}`
- SK: `{timestamp}#{decision_id}`
- GSI1 (SuccessIndex): Query by success/failure
- GSI2 (DecisionTypeIndex): Query by decision type
- GSI3 (STMIndex): Query STM vs LTM
- TTL: Auto-expire old decisions

**agent_memory_ltm**
- Stores long-term patterns
- PK: `agent:{agent_id}#{memory_type}`
- SK: `{pattern_id}`
- GSI1 (ConfidenceIndex): Sort by confidence
- GSI2 (SharedPatternIndex): Query shared patterns

**agent_state**
- Stores agent state
- PK: `agent:{agent_id}`
- SK: `{state_type}`
- Types: CURRENT, CHECKPOINT, BACKUP, ROLLBACK

**agent_signals**
- Stores cross-agent signals
- PK: `signal#{type}`
- SK: `{timestamp}#{signal_id}`
- GSI1 (TargetAgentIndex): Query by target agent
- TTL: Auto-expire after 24 hours

### Memory Timeline

- **Short-Term Memory (STM)**: Decisions < 1 day old, `is_stm=True`
  - Frequent access expected
  - Auto-cleanup after 24-72 hours
  - Used for immediate context

- **Long-Term Memory (LTM)**: Patterns > 1 day old, stored as MemoryPattern
  - Persistent storage
  - Confidence and success rate tracking
  - Used for strategic learning

## 📈 Cost Optimization

**Demo Configuration** (~$3.50/month):
- DynamoDB On-Demand pricing
- 144 cycles/day × 30 days = 4,320 cycles/month
- ~50 reads + 20 writes per cycle
- Total: 216K reads + 86K writes = ~$3.50/month

**Production with DAX** (~$51.50/month):
- Add DAX t3.small instance: ~$48/month
- Sub-millisecond reads for hot data
- Easy migration: just add DAX endpoint

## 🧪 Testing

Run the example script:

```bash
python examples/memory_system_demo.py
```

This demonstrates:
- Decision logging with outcomes
- Pattern storage and retrieval
- State management with checkpoints
- Signal publishing and consumption
- Cleanup operations

## 📚 Documentation

See `docs/memory/` for comprehensive documentation:
- **IMPLEMENTATION_PLAN.md**: Complete architecture
- **QUICKSTART.md**: One-page reference
- **DECISION_NO_DAX_FOR_DEMO.md**: Cost analysis
- **READY_TO_BUILD.md**: Build summary

## 🛠️ Next Steps

### Phase 2: Decision Logging Integration
- Integrate DecisionLogger with IntegratedMarketHunterAgent
- Log all decision points
- Test end-to-end decision flow

### Phase 3: Multi-Agent Coordination
- Create MultiAgentCoordinator
- Implement agent registry
- Test multi-agent scenarios

### Phase 4: Pattern Learning
- Create PatternLearner for automatic pattern discovery
- Implement STM→LTM consolidation jobs
- Add pattern evolution and versioning

### Phase 5: Analytics & Production
- Build analytics dashboards
- CloudWatch integration
- Production deployment

## 🔑 Key Design Decisions

1. **DynamoDB without DAX for demo**: Cost-optimized ($3.50/month vs $51.50/month)
2. **Multi-agent from day 1**: Partition keys include agent_id throughout
3. **Memory timeline > 1 day = LTM**: Decisions older than 1 day become patterns
4. **User metadata placeholder**: `MemoryPattern.user_metadata` ready for custom pattern fields
5. **Pydantic validation**: Type safety and data integrity
6. **GSI strategy**: Efficient queries without scans

## 📝 License

Part of the AWS BTC Agent project.

## 🤝 Contributing

See main project README for contribution guidelines.
