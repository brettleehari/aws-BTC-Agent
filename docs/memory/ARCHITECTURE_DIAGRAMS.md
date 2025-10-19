# Memory System Architecture Diagrams

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Agent Application                    │
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │                  │    │                  │               │
│  │ IntegratedMarket │    │ MultiAgent       │               │
│  │ HunterAgent      │    │ Coordinator      │               │
│  │                  │    │                  │               │
│  └────────┬─────────┘    └────────┬─────────┘               │
│           │                       │                          │
│           └───────────┬───────────┘                          │
│                       │                                      │
│  ┌────────────────────▼───────────────────────┐              │
│  │                                             │              │
│  │           DecisionLogger                    │              │
│  │                                             │              │
│  │  - log_decision()                           │              │
│  │  - log_outcome()                            │              │
│  │  - get_decision_stats()                     │              │
│  │  - get_decision_chain()                     │              │
│  │                                             │              │
│  └─────────────────────┬───────────────────────┘              │
│                        │                                      │
│  ┌─────────────────────▼────────────────────┐                │
│  │                                           │                │
│  │         MemoryManager                     │                │
│  │                                           │                │
│  │  - store_decision()                       │                │
│  │  - query_decisions()                      │                │
│  │  - store_pattern()                        │                │
│  │  - query_patterns()                       │                │
│  │  - save_state()                           │                │
│  │  - load_state()                           │                │
│  │  - publish_signal()                       │                │
│  │  - get_pending_signals()                  │                │
│  │                                           │                │
│  └─────────────────────┬─────────────────────┘                │
│                        │                                      │
│  ┌─────────────────────▼────────────────────┐                │
│  │                                           │                │
│  │      AWSClientManager                     │                │
│  │                                           │                │
│  │  - dynamodb_resource                      │                │
│  │  - dynamodb_client                        │                │
│  │  - cloudwatch                             │                │
│  │  - create_all_tables()                    │                │
│  │                                           │                │
│  └─────────────────────┬─────────────────────┘                │
└────────────────────────┼──────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │                                │
        │         AWS Services           │
        │                                │
        │  ┌──────────────────────────┐  │
        │  │  DynamoDB Tables         │  │
        │  │  ┌────────────────────┐  │  │
        │  │  │ agent_decisions    │  │  │
        │  │  │ (3 GSIs)           │  │  │
        │  │  └────────────────────┘  │  │
        │  │  ┌────────────────────┐  │  │
        │  │  │ agent_memory_ltm   │  │  │
        │  │  │ (2 GSIs)           │  │  │
        │  │  └────────────────────┘  │  │
        │  │  ┌────────────────────┐  │  │
        │  │  │ agent_state        │  │  │
        │  │  └────────────────────┘  │  │
        │  │  ┌────────────────────┐  │  │
        │  │  │ agent_signals      │  │  │
        │  │  │ (1 GSI)            │  │  │
        │  │  └────────────────────┘  │  │
        │  └──────────────────────────┘  │
        │                                │
        │  ┌──────────────────────────┐  │
        │  │  CloudWatch Metrics      │  │
        │  └──────────────────────────┘  │
        │                                │
        └────────────────────────────────┘
```

## Decision Flow

```
Agent Execution Cycle
    │
    ├─► Source Selection Decision
    │   │
    │   ├─► log_decision(SOURCE_SELECTION)
    │   │   ├── Context: market, cycle, trading_hours
    │   │   ├── Reasoning: scores, selected, confidence
    │   │   └── Store to DynamoDB (is_stm=True)
    │   │
    │   ├─► Execute Source Selection
    │   │
    │   └─► log_outcome(success, quality_score, latency)
    │       └── Update decision record
    │
    ├─► Query Execution Decision
    │   │
    │   ├─► log_decision(QUERY_EXECUTION, parent_id)
    │   ├─► Execute Queries
    │   └─► log_outcome()
    │
    ├─► Signal Generation Decision
    │   │
    │   ├─► log_decision(SIGNAL_GENERATION, parent_id)
    │   ├─► Generate Signals
    │   └─► log_outcome(signals_generated=[...])
    │
    └─► End of Cycle
        │
        ├─► Save Agent State
        │   └── save_state(CURRENT)
        │
        └─► Query Decision Stats
            └── get_decision_stats(time_window_hours=24)
```

## Memory Timeline

```
Time ──────────────────────────────────────────────►

│◄──── Short-Term Memory (STM) ────►│◄──── Long-Term Memory (LTM) ────►│
│                                   │                                   │
│         < 1 day                   │         > 1 day                   │
│                                   │                                   │
│  ┌─────────────────────┐          │  ┌─────────────────────┐          │
│  │  DecisionRecord     │          │  │  MemoryPattern      │          │
│  │  is_stm=True        │          │  │                     │          │
│  │                     │          │  │  confidence: 0.85   │          │
│  │  - Frequent access  │          │  │  success_rate: 0.78 │          │
│  │  - Auto-expire      │   ──►   │  │  sample_size: 120   │          │
│  │  - Immediate ctx    │  Consol- │  │                     │          │
│  │  - High volume      │  idation │  │  - Persistent       │          │
│  │                     │          │  │  - Pattern learning │          │
│  └─────────────────────┘          │  │  - Strategic use    │          │
│                                   │  └─────────────────────┘          │
│                                   │                                   │
│  Cleanup after 24-72 hours        │  Permanent storage                │
│                                   │                                   │
```

## Multi-Agent Communication

```
Agent 1                          Agent 2                          Agent 3
   │                                │                                │
   │  Detect Whale Activity         │                                │
   │  (1500 BTC transfer)           │                                │
   │                                │                                │
   ├─► publish_signal()             │                                │
   │   ├── SignalType: WHALE_ACTIVITY                               │
   │   ├── target_agents: [agent-2, agent-3]                        │
   │   ├── confidence: 0.92                                          │
   │   └── Store to agent_signals table ─────────┐                  │
   │                                              │                  │
   │                                              ▼                  │
   │                                   ┌──────────────────┐          │
   │                                   │ agent_signals    │          │
   │                                   │ PK: signal#type  │          │
   │                                   │ GSI: target_agent│          │
   │                                   └──────────────────┘          │
   │                                              │                  │
   │                                              ├──────────────────┤
   │                                              │                  │
   │                                              ▼                  ▼
   │                                    get_pending_signals()  get_pending_signals()
   │                                              │                  │
   │                                    ┌─────────┴──────┐  ┌────────┴─────┐
   │                                    │ Process signal │  │ Process signal│
   │                                    │                │  │               │
   │                                    │ - Adjust risk  │  │ - Update ctx  │
   │                                    │ - Update state │  │ - Log decision│
   │                                    └────────┬───────┘  └───────┬───────┘
   │                                             │                   │
   │                                             ▼                   ▼
   │                                    mark_signal_processed() mark_signal_processed()
   │                                    status='PROCESSED'      status='PROCESSED'
   │
```

## Data Model Relationships

```
DecisionRecord
├── decision_id (unique)
├── agent_id
├── decision_type (enum)
├── timestamp
├── context (DecisionContext)
│   ├── market (dict)
│   ├── cycle (int)
│   ├── trading_hours (bool)
│   ├── parent_decision_id ──┐   (Decision chain)
│   └── agent_state (dict)    │
│                             │
├── reasoning (DecisionReasoning)
│   ├── scores (dict)         │
│   ├── selected (list)       │
│   ├── memory_influenced (bool) ──► Indicates pattern usage
│   ├── patterns_applied (list) ───► References MemoryPattern IDs
│   ├── exploration (bool)    │
│   └── confidence (float)    │
│                             │
├── outcome (DecisionOutcome) │
│   ├── success (bool)        │
│   ├── signals_generated (list) ──► References AgentSignal IDs
│   ├── quality_score (float) │
│   ├── latency_ms (float)    │
│   ├── errors (list)         │
│   └── metrics (dict)        │
│                             │
├── is_stm (bool)             │
└── ttl (int)                 │
                              │
                              │
MemoryPattern                 │
├── pattern_id (unique)       │
├── agent_id                  │
├── memory_type (enum)        │
├── learned_at                │
├── last_accessed             │
├── access_count              │
├── confidence (float)        │
├── success_rate (float)      │
├── sample_size (int)         │
├── data (dict)               │
├── user_metadata (dict) ◄────┼── TO BE POPULATED BY USER
├── version (int)             │
├── is_shared (bool)          │
└── shared_with (list)        │
                              │
                              │
AgentState                    │
├── agent_id                  │
├── agent_version             │
├── state_type (enum)         │
├── status (enum)             │
├── current_cycle             │
├── last_updated              │
├── source_metrics (dict)     │
├── context_performance (dict)│
├── configuration (dict)      │
└── version (int)             │
                              │
                              │
AgentSignal                   │
├── signal_id (unique)        │
├── signal_type (enum)        │
├── source_agent ─────────────┘
├── target_agents (list)
├── timestamp
├── severity (enum)
├── confidence (float)
├── data (dict)
├── context (dict)
├── recommended_action (str)
├── processing_status (dict) ──► {agent_id: status}
└── ttl (int)
```

## DynamoDB Access Patterns

```
agent_decisions Table
├── Access Pattern 1: Get all decisions for an agent by type
│   Query: PK = "agent:{id}#decision#{type}", SK begins_with ""
│
├── Access Pattern 2: Get successful/failed decisions
│   Query GSI1 (SuccessIndex): GSI1_PK = "agent:{id}#success:true"
│
├── Access Pattern 3: Get decisions by type across agents
│   Query GSI2 (DecisionTypeIndex): GSI2_PK = "decision:{type}"
│
└── Access Pattern 4: Get STM vs LTM decisions
    Query GSI3 (STMIndex): GSI3_PK = "agent:{id}#stm:true"


agent_memory_ltm Table
├── Access Pattern 1: Get all patterns for an agent by type
│   Query: PK = "agent:{id}#{memory_type}", SK begins_with ""
│
├── Access Pattern 2: Get high-confidence patterns
│   Query GSI1 (ConfidenceIndex): GSI1_PK = "agent:{id}", Sort by GSI1_SK desc
│
└── Access Pattern 3: Get shared patterns
    Query GSI2 (SharedPatternIndex): GSI2_PK = "shared:true", Filter by shared_with


agent_state Table
├── Access Pattern 1: Get current state
│   Get: PK = "agent:{id}", SK = "CURRENT"
│
├── Access Pattern 2: Get checkpoint
│   Get: PK = "agent:{id}", SK = "CHECKPOINT"
│
└── Access Pattern 3: Get all state versions
    Query: PK = "agent:{id}", SK begins_with ""


agent_signals Table
├── Access Pattern 1: Get signals by type
│   Query: PK = "signal#{type}", SK begins_with ""
│
└── Access Pattern 2: Get signals for a target agent
    Query GSI1 (TargetAgentIndex): GSI1_PK = "target:{agent_id}"
```

## Cost Breakdown (Demo)

```
Monthly Cost Estimate: $3.50/month

Breakdown:
├── Reads: 216,000 read units @ $0.25/million = $0.05
├── Writes: 86,400 write units @ $1.25/million = $0.11
├── Storage: 1 GB @ $0.25/GB = $0.25
└── Additional overhead = ~$3.09

Activity:
├── 144 cycles/day × 30 days = 4,320 cycles/month
├── ~50 reads per cycle (decisions, patterns, state, signals)
├── ~20 writes per cycle (new decisions, updates, state saves)
└── Total: 216K reads + 86K writes

Scaling:
├── Add DAX t3.small: +$48/month → $51.50/month total
│   └── Sub-millisecond latency for hot data
├── Production workload (1000 cycles/day): ~$15/month
└── Enterprise (10,000 cycles/day): ~$80/month
```

## System Flow Summary

```
1. Agent makes decision
   └─► DecisionLogger.log_decision()
       └─► MemoryManager.store_decision()
           └─► DynamoDB: agent_decisions

2. Agent executes decision
   └─► DecisionLogger.log_outcome()
       └─► MemoryManager.store_decision() (update)
           └─► DynamoDB: agent_decisions (same item)

3. Agent learns pattern
   └─► MemoryManager.store_pattern()
       └─► DynamoDB: agent_memory_ltm

4. Agent saves state
   └─► MemoryManager.save_state()
       └─► DynamoDB: agent_state

5. Agent publishes signal
   └─► MemoryManager.publish_signal()
       └─► DynamoDB: agent_signals

6. Other agents consume signal
   └─► MemoryManager.get_pending_signals()
       └─► DynamoDB Query: GSI1 (TargetAgentIndex)
           └─► Filter: processing_status[agent_id] = 'PENDING'

7. Cleanup (scheduled)
   └─► MemoryManager.cleanup_stm(older_than_hours=24)
       └─► DynamoDB: Delete old STM decisions
           └─► (Note: TTL also auto-expires)
```
