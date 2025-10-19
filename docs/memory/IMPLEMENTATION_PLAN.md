# Agent Memory System - Implementation Plan
## Based on Finalized Requirements

## Decision Summary

✅ **Storage Strategy**: DynamoDB + DAX (unified, simpler)
✅ **Implementation Scope**: Full system (STM + LTM + Analytics)
✅ **Budget**: Demo/POC budget (cost-optimized)
✅ **Multi-Agent**: Design for multiple agents from day 1
✅ **Memory Timeline**: 
   - < 1 day = Short-term (DAX cache)
   - > 1 day = Long-term (DynamoDB)

---

## Simplified Architecture with DynamoDB DAX

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Market       │  │ Risk         │  │ Trading      │          │
│  │ Hunter       │  │ Manager      │  │ Executor     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │                                     │
└────────────────────────────┼─────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              UNIFIED MEMORY & LOGGING LAYER                      │
│  ┌──────────────────┐          ┌──────────────────┐            │
│  │ Memory Manager   │          │ Decision Logger  │            │
│  │ - STM (< 1 day)  │          │ - All decisions  │            │
│  │ - LTM (> 1 day)  │          │ - Outcomes       │            │
│  │ - Multi-agent    │          │ - Multi-agent    │            │
│  └────────┬─────────┘          └────────┬─────────┘            │
│           │                              │                       │
└───────────┼──────────────────────────────┼───────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AWS STORAGE LAYER (SIMPLIFIED)                  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              DynamoDB with DAX Cluster                     │ │
│  │                                                            │ │
│  │  DAX (In-Memory Cache)          DynamoDB (Persistent)     │ │
│  │  ┌──────────────────┐          ┌──────────────────────┐  │ │
│  │  │ < 1 day (STM)    │          │ agent_decisions      │  │ │
│  │  │ - Context        │  ←sync→  │ - All decisions      │  │ │
│  │  │ - Recent queries │          │ - TTL after 90 days  │  │ │
│  │  │ - Active signals │          └──────────────────────┘  │ │
│  │  │ - Rate limits    │                                     │ │
│  │  └──────────────────┘          ┌──────────────────────┐  │ │
│  │                                 │ agent_memory_ltm     │  │ │
│  │  Auto-eviction:                 │ - Patterns           │  │ │
│  │  Data older than 1 day          │ - Strategies         │  │ │
│  │  moves to DynamoDB only         │ - No TTL             │  │ │
│  │                                 └──────────────────────┘  │ │
│  │                                                            │ │
│  │                                 ┌──────────────────────┐  │ │
│  │                                 │ agent_state          │  │ │
│  │                                 │ - Current state      │  │ │
│  │                                 │ - Config             │  │ │
│  │                                 └──────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              S3 (Archive - Optional for Demo)             │ │
│  │  - Cold storage for decisions > 90 days                   │ │
│  │  - Can be added later if needed                           │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## DynamoDB + DAX Benefits

### Why DAX for This Use Case:

1. **Unified Service**: Single AWS service (DynamoDB) + caching layer
2. **Microsecond Latency**: DAX provides sub-millisecond reads
3. **Simplified Architecture**: No need to manage Redis separately
4. **Automatic Cache**: DAX automatically caches hot data
5. **Write-Through**: Writes go through DAX to DynamoDB (consistency)
6. **Cost-Effective for Demo**: t3.small DAX node = ~$40/month vs Redis ~$12/month but simpler ops

### Trade-offs Accepted:

- Slightly higher cost than Redis (~$40 vs ~$12) but simpler to manage
- Less flexible cache eviction policies (vs Redis TTL)
- Worth it for unified service and simplified architecture

---

## Multi-Agent Design from Day 1

### Agent Identification Strategy

Every piece of data is tagged with `agent_id`:

```python
# Examples
agent_ids = [
    "market-hunter",      # Market intelligence
    "risk-manager",       # Risk assessment
    "trade-executor",     # Trade execution
    "portfolio-optimizer", # Portfolio management
    "sentiment-analyzer"  # Social sentiment
]
```

### Shared vs Private Memory

```python
# Partition Key Design for Multi-Agent
PK_PATTERNS = {
    # Private: Agent-specific decisions
    "private_decision": "agent:{agent_id}#decision#{type}",
    
    # Private: Agent-specific memory
    "private_memory": "agent:{agent_id}#memory#{type}",
    
    # Shared: Cross-agent communication
    "shared_signal": "shared#signal#{type}",
    
    # Shared: Global patterns
    "shared_pattern": "shared#pattern#{domain}"
}

# Example:
# PK = "agent:market-hunter#decision#SOURCE_SELECTION"
# PK = "agent:risk-manager#decision#RISK_ASSESSMENT"
# PK = "shared#signal#WHALE_ACTIVITY"
```

### Agent Communication via Memory

```python
# Market Hunter writes signal
await memory.store_shared_signal({
    "signal_id": "sig_123",
    "source_agent": "market-hunter",
    "signal_type": "WHALE_ACTIVITY",
    "confidence": 0.85,
    "target_agents": ["risk-manager", "trade-executor"],
    "data": {"whale_count": 5, "total_btc": 5000}
})

# Risk Manager reads signals
signals = await memory.get_signals_for_agent("risk-manager")
# Returns signals where target_agents contains "risk-manager"
```

---

## DynamoDB Table Schemas (Multi-Agent)

### Table 1: `agent_decisions` (All Agents)

```python
{
    # Partition Key: agent_id + decision_type
    "PK": "agent:market-hunter#decision#SOURCE_SELECTION",
    
    # Sort Key: timestamp + decision_id
    "SK": "2025-10-18T14:30:00Z#dec_abc123",
    
    # Attributes
    "agent_id": "market-hunter",
    "agent_version": "1.0.0",
    "decision_id": "dec_abc123",
    "decision_type": "SOURCE_SELECTION",
    "timestamp": 1729260600,  # Unix timestamp
    "iso_timestamp": "2025-10-18T14:30:00Z",
    
    "context": {
        "market": {"volatility": "high", "trend": "bullish"},
        "cycle": 142,
        "trading_hours": "american",
        "parent_decision_id": None  # For decision chains
    },
    
    "reasoning": {
        "scores": {"whaleMovements": 0.92, "derivatives": 0.87},
        "selected": ["whaleMovements", "derivatives"],
        "memory_influenced": True,
        "patterns_applied": ["pattern_whale_pump"]
    },
    
    "outcome": {
        "success": True,
        "signals_generated": 2,
        "quality_score": 0.85,
        "latency_ms": 1200,
        "errors": []
    },
    
    # TTL for automatic cleanup (90 days from now)
    "ttl": 1737036600,
    
    # STM indicator (< 1 day old)
    "is_stm": True  # Updated by Lambda to False after 1 day
}

# GSI 1: Query by agent + success
{
    "GSI1_PK": "agent:market-hunter#success",
    "GSI1_SK": timestamp
}

# GSI 2: Query by decision type across agents
{
    "GSI2_PK": "decision_type#SOURCE_SELECTION",
    "GSI2_SK": timestamp
}

# GSI 3: Query recent decisions (STM)
{
    "GSI3_PK": "agent:market-hunter#stm",
    "GSI3_SK": timestamp
}
```

### Table 2: `agent_memory_ltm` (All Agents)

```python
{
    # Partition Key: agent_id + memory_type
    "PK": "agent:market-hunter#pattern",
    
    # Sort Key: pattern_id
    "SK": "pattern_whale_pump_correlation",
    
    # Attributes
    "agent_id": "market-hunter",
    "memory_type": "PATTERN",
    "pattern_id": "pattern_whale_pump_correlation",
    
    "learned_at": 1729260600,
    "last_accessed": 1729346600,
    "access_count": 45,
    
    "confidence": 0.85,
    "success_rate": 0.78,
    "sample_size": 23,
    
    "data": {
        "description": "Whale movements > 5 predict 70%+ pump in bullish trends",
        "conditions": {
            "context": "bullish_trend",
            "whale_count_min": 5,
            "timeframe": "4h"
        },
        "outcomes": {
            "pump_probability": 0.78,
            "avg_pump_pct": 3.2,
            "timeframe": "4-8h after detection"
        }
    },
    
    "version": 3,  # Pattern can evolve
    
    # Shared pattern (accessible by other agents)
    "is_shared": False,
    "shared_with": []  # List of agent_ids if shared
}

# GSI 1: Query by confidence
{
    "GSI1_PK": "agent:market-hunter#pattern",
    "GSI1_SK": confidence  # High to low
}

# GSI 2: Query shared patterns
{
    "GSI2_PK": "shared_pattern#domain",
    "GSI2_SK": confidence
}
```

### Table 3: `agent_state` (All Agents)

```python
{
    # Partition Key: agent_id
    "PK": "agent:market-hunter",
    
    # Sort Key: state_type
    "SK": "CURRENT",
    
    # Attributes
    "agent_id": "market-hunter",
    "agent_version": "1.0.0",
    "state_type": "CURRENT",  # or "CHECKPOINT", "BACKUP"
    
    "current_cycle": 142,
    "last_updated": 1729260600,
    
    "source_metrics": {
        "whaleMovements": {
            "success_rate": 0.85,
            "quality_score": 0.78,
            "total_calls": 1523,
            "last_used_cycles": 0
        }
        # ... other sources
    },
    
    "context_performance": {
        "high_volatility": {
            "whaleMovements": 0.92,
            "derivatives": 0.87
        }
        # ... other contexts
    },
    
    "configuration": {
        "learning_rate": 0.1,
        "exploration_rate": 0.2,
        "technical_weight": 0.7
    },
    
    "version": 156  # Incremented on each update
}
```

### Table 4: `agent_signals` (Multi-Agent Communication)

```python
{
    # Partition Key: signal_type
    "PK": "signal#WHALE_ACTIVITY",
    
    # Sort Key: timestamp
    "SK": "2025-10-18T14:30:00Z#sig_xyz789",
    
    # Attributes
    "signal_id": "sig_xyz789",
    "signal_type": "WHALE_ACTIVITY",
    "source_agent": "market-hunter",
    "target_agents": ["risk-manager", "trade-executor"],
    
    "timestamp": 1729260600,
    "iso_timestamp": "2025-10-18T14:30:00Z",
    
    "severity": "high",
    "confidence": 0.85,
    
    "data": {
        "whale_count": 5,
        "total_btc": 5000,
        "direction": "accumulation",
        "exchanges": ["binance", "coinbase"]
    },
    
    "context": {
        "market_condition": "bullish",
        "volatility": "high"
    },
    
    "recommended_action": "MONITOR_CLOSELY",
    
    # Processing status by each target agent
    "processing_status": {
        "risk-manager": {
            "status": "PROCESSED",
            "processed_at": 1729260650,
            "decision_id": "dec_risk_001"
        },
        "trade-executor": {
            "status": "PENDING",
            "processed_at": None
        }
    },
    
    # TTL: 24 hours (signals are ephemeral)
    "ttl": 1729347000
}

# GSI 1: Query by target agent
{
    "GSI1_PK": "target_agent:risk-manager",
    "GSI1_SK": timestamp
}
```

---

## Cost Optimization for Demo Budget

### Minimal Production Setup

```yaml
DynamoDB Tables:
  - On-Demand Pricing (pay per request)
  - No provisioned capacity
  - Auto-scaling not needed for demo
  
DAX Cluster:
  - 1 node: dax.t3.small (2 vCPU, 1.5 GB)
  - Cost: $0.067/hour = ~$48/month
  - Can use t2.small for even less: ~$35/month
  
S3 (Optional):
  - Skip for demo
  - Add later if archival needed
  
CloudWatch:
  - Basic metrics (free tier)
  - Minimal custom metrics

Total Monthly Cost: $40-50/month
```

### Cost Reduction Options:

1. **Use DynamoDB without DAX initially**: $5-10/month
   - Add DAX later when performance matters
   - Good for POC/demo phase

2. **TTL Aggressive Cleanup**: 7 days instead of 90 days
   - Reduces storage costs
   - Still enough for pattern learning

3. **On-Demand Pricing**: Only pay for actual usage
   - Perfect for demo with variable traffic

---

## File Structure

```
src/
├── memory/
│   ├── __init__.py
│   ├── models.py                    # Pydantic models for all schemas
│   ├── aws_clients.py               # DynamoDB + DAX client management
│   ├── memory_manager.py            # Core memory operations
│   ├── decision_logger.py           # Decision logging
│   ├── multi_agent_coordinator.py   # Multi-agent communication
│   ├── pattern_learner.py           # Pattern identification
│   ├── analytics.py                 # Performance analytics
│   └── utils.py                     # Helper functions
│
├── agents/
│   ├── __init__.py
│   ├── base_memory_aware_agent.py   # Base class for all agents
│   ├── market_hunter_memory.py      # Memory-aware Market Hunter
│   └── agent_registry.py            # Register all agents
│
└── deployment/
    ├── dynamodb_setup.py            # Create tables
    ├── dax_setup.py                 # Create DAX cluster (optional)
    └── cleanup.py                   # Cleanup resources

tests/
├── test_memory/
│   ├── test_memory_manager.py
│   ├── test_decision_logger.py
│   ├── test_multi_agent.py
│   └── test_pattern_learner.py
│
└── test_integration/
    └── test_full_memory_cycle.py

docs/
└── memory/
    ├── ARCHITECTURE.md              # This file
    ├── API_REFERENCE.md             # API documentation
    ├── DEPLOYMENT.md                # Deployment guide
    └── PATTERNS.md                  # Pattern documentation (user will add)
```

---

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
**Goal**: Basic infrastructure and models

```
Day 1:
✅ Create directory structure
✅ Define Pydantic models (models.py)
✅ Create AWS client helpers (aws_clients.py)
✅ Write DynamoDB table creation script
✅ Basic unit tests

Day 2:
✅ Implement MemoryManager (STM/LTM operations)
✅ Test DynamoDB operations locally (DynamoDB Local)
✅ Integration tests
```

### Phase 2: Decision Logging (Days 3-4)
**Goal**: Log all agent decisions

```
Day 3:
✅ Implement DecisionLogger class
✅ Add decision types enum
✅ Create query helpers
✅ Unit tests

Day 4:
✅ Integrate with IntegratedMarketHunterAgent
✅ Log all decision points
✅ Test logging flow
✅ Verify DynamoDB writes
```

### Phase 3: Multi-Agent Support (Days 5-6)
**Goal**: Enable multi-agent communication

```
Day 5:
✅ Implement MultiAgentCoordinator
✅ Signal publishing/subscribing
✅ Agent registry
✅ Shared memory operations

Day 6:
✅ Test multi-agent scenarios
✅ Create example agents
✅ Integration tests
```

### Phase 4: Pattern Learning (Days 7-8)
**Goal**: Automatic pattern identification

```
Day 7:
✅ Implement PatternLearner
✅ Pattern identification algorithms
✅ Confidence calculation
✅ Pattern promotion (STM → LTM)

Day 8:
✅ Consolidation jobs
✅ Pattern querying
✅ Pattern evolution (version updates)
✅ Tests
```

### Phase 5: Analytics & Production (Days 9-10)
**Goal**: Deploy and monitor

```
Day 9:
✅ Implement Analytics class
✅ Performance dashboards
✅ CloudWatch integration
✅ Cost monitoring

Day 10:
✅ Deploy to AWS
✅ DAX cluster setup (optional)
✅ Production testing
✅ Documentation
```

---

## Next Steps

### Immediate Actions:

1. **Create base directory structure**
   ```bash
   mkdir -p src/memory tests/test_memory docs/memory
   ```

2. **Define Pydantic models** (schemas)
   - DecisionRecord
   - MemoryPattern
   - AgentState
   - Signal

3. **Create AWS client helpers**
   - DynamoDB client with retry logic
   - DAX client (optional for demo)
   - Table creation scripts

4. **Start with MemoryManager**
   - Basic CRUD operations
   - Multi-agent support from start

### Questions Remaining:

1. **Pattern Details**: You mentioned you'll provide pattern details later - when ready, we'll add to `docs/memory/PATTERNS.md`

2. **DAX for Demo**: Since budget is demo/POC, should we:
   - **Option A**: Start without DAX, add later if needed ($5-10/month)
   - **Option B**: Include DAX from start for full experience ($40-50/month)
   - **Recommendation**: Start without DAX, DynamoDB is fast enough for demo

3. **Agent Priority**: Which agents to build first?
   - Market Hunter (already exists, enhance with memory)
   - Risk Manager (new)
   - Trade Executor (new)
   - **Recommendation**: Start with Market Hunter memory integration

---

## Summary

✅ **Storage**: DynamoDB + optional DAX
✅ **Design**: Multi-agent from day 1
✅ **Memory**: < 1 day = STM (cached), > 1 day = LTM
✅ **Timeline**: 10 days for full implementation
✅ **Cost**: $5-10/month without DAX, $40-50/month with DAX

**Ready to start implementing?** Let me know if you want to begin with the foundation phase! 🚀
