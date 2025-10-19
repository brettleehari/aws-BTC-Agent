# 🚀 Memory System - Quick Reference

**Status:** ✅ Phase 1 Complete | **Ready:** Yes | **Cost:** ~$4/month

---

## Setup (3 commands)

```bash
pip install boto3 pydantic pytest pytest-asyncio
aws configure  # or: docker run -p 8000:8000 amazon/dynamodb-local
python deployment/dynamodb_setup.py create
```

## Verify (2 commands)

```bash
python deployment/dynamodb_setup.py status
pytest tests/test_memory/ -v
```

---

## Core APIs

### Log Decisions
```python
from src.memory import DecisionLogger
from src.memory.models import DecisionContext, DecisionReasoning, DecisionOutcome
from src.memory.enums import DecisionType

logger = DecisionLogger()

# Log
decision_id = await logger.log_decision(
    agent_id="market-hunter",
    decision_type=DecisionType.SOURCE_SELECTION,
    decision_made="Selected coindesk",
    context=DecisionContext(market_conditions={}, agent_state={}, available_resources=[]),
    reasoning=DecisionReasoning(confidence_score=0.85, alternative_options=[], risk_assessment={})
)

# Update
await logger.log_outcome(decision_id, DecisionOutcome(success=True, actual_result={}, execution_time_ms=150))

# Query
decisions = await logger.query_decisions(agent_id="market-hunter", success_filter=True)
```

### Store Patterns
```python
from src.memory import MemoryManager
from src.memory.models import MemoryPattern
from src.memory.enums import MemoryType

memory = MemoryManager()

# Store
pattern = MemoryPattern(
    pattern_id="p1", agent_id="hunter", memory_type=MemoryType.PATTERN,
    name="Bullish divergence", description="RSI divergence pattern",
    data={"indicators": ["RSI"]}, confidence=0.82,
    last_updated=datetime.now(timezone.utc), version=1
)
await memory.store_pattern(pattern)

# Query
patterns = await memory.query_patterns(agent_id="hunter", min_confidence=0.8)
```

### Agent State
```python
from src.memory.models import AgentState
from src.memory.enums import AgentStatus, StateType

# Save
state = AgentState(
    agent_id="hunter", timestamp=datetime.now(timezone.utc),
    state_type=StateType.CURRENT, status=AgentStatus.ACTIVE,
    current_cycle=5, performance_metrics={}, configuration={}
)
await memory.save_state(state)

# Get
current = await memory.get_agent_state("hunter")
```

### Publish Signals
```python
from src.memory.models import AgentSignal
from src.memory.enums import SignalType, SignalSeverity, ProcessingStatus

# Publish
signal = AgentSignal(
    signal_id="s1", source_agent_id="hunter", target_agent_id="risk-mgr",
    signal_type=SignalType.WHALE_ACTIVITY, severity=SignalSeverity.HIGH,
    timestamp=datetime.now(timezone.utc), data={"amount": 1000},
    processing_status=ProcessingStatus.PENDING
)
await memory.publish_signal(signal)

# Retrieve
signals = await memory.get_signals_for_agent(agent_id="risk-mgr")
```

---

## Table Management

```bash
# Create all tables (AWS)
python deployment/dynamodb_setup.py create

# Create locally
python deployment/dynamodb_setup.py create --local

# Check status
python deployment/dynamodb_setup.py status

# Delete all (⚠️ irreversible!)
python deployment/dynamodb_setup.py delete
```

---

## Testing

```bash
# Unit tests (11 tests)
pytest tests/test_memory/test_models.py -v

# Integration tests (6 scenarios)
python tests/test_memory/test_integration.py

# All tests
pytest tests/test_memory/ -v
```

---

## File Locations

| What | Where |
|------|-------|
| **Core Code** | `src/memory/` (8 files, 2,015 lines) |
| **Tables** | `deployment/dynamodb_setup.py` |
| **Tests** | `tests/test_memory/` (17 tests) |
| **Docs** | `docs/memory/` (11 documents) |
| **Setup Guide** | `docs/memory/PHASE1_SETUP.md` |
| **Validation** | `docs/memory/VALIDATION_CHECKLIST.md` |
| **Summary** | `MEMORY_SYSTEM_COMPLETE.md` |

---

## Database Tables

| Table | Key | GSIs | Purpose |
|-------|-----|------|---------|
| `agent_decisions` | decision_id | 3 | Decisions with context/outcomes |
| `agent_memory_ltm` | pattern_id | 3 | Long-term patterns |
| `agent_state` | agent_id + timestamp | 2 | Agent state/checkpoints |
| `agent_signals` | signal_id | 3 | Cross-agent signals |

---

## Common Commands

```python
# STM (< 1 day)
stm = await memory.query_recent_decisions(agent_id="hunter", hours=24)

# LTM (all time)
ltm = await memory.query_decisions(agent_id="hunter", start_time=week_ago)

# Success rate
rate = await logger.get_success_rate(agent_id="hunter", decision_type=DecisionType.SOURCE_SELECTION)

# Decision chain
chain = await logger.get_decision_chain(decision_id)

# Update pattern confidence
await memory.update_pattern_confidence(pattern_id, new_confidence=0.9)
```

---

## Enums Quick Reference

```python
from src.memory.enums import (
    DecisionType,        # SOURCE_SELECTION, QUERY_EXECUTION, SIGNAL_GENERATION, etc.
    MemoryType,          # PATTERN, STRATEGY, ARCHETYPE, CONTEXT, METRIC
    SignalType,          # WHALE_ACTIVITY, POSITIVE_NARRATIVE, REGULATORY_CHANGE, etc.
    SignalSeverity,      # LOW, MEDIUM, HIGH, CRITICAL
    ProcessingStatus,    # PENDING, PROCESSED, FAILED, EXPIRED
    AgentStatus,         # ACTIVE, IDLE, ERROR, STOPPED, MAINTENANCE
    StateType,           # CURRENT, CHECKPOINT, BACKUP
)
```

---

## Costs

- **DynamoDB On-Demand:** ~$3.50/month
- **Storage (25 GB):** Free
- **CloudWatch:** < $1/month
- **Total:** ~$4-5/month

---

## Next Steps

1. **Test locally:** Use DynamoDB Local
2. **Deploy to AWS:** Create tables in AWS
3. **Integrate:** Add to your agents
4. **Monitor:** Check table sizes regularly

---

## Documentation

- `PHASE1_SETUP.md` - Complete setup instructions
- `VALIDATION_CHECKLIST.md` - Verify installation
- `GAP_ANALYSIS.md` - What's implemented
- `MEMORY_SYSTEM_COMPLETE.md` - Full summary

---

## Support

```bash
# Check imports
python -c "from src.memory import DecisionLogger; print('✅ OK')"

# Check tables
python deployment/dynamodb_setup.py status

# Run tests
pytest tests/test_memory/ -v

# Manual test
python test_manual.py
```

---

**Everything working?** ✅ You're ready to integrate!

**Need help?** See `docs/memory/PHASE1_SETUP.md`
