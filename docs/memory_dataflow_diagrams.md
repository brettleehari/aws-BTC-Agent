# Agent Memory & Decision Logging - Data Flow Diagrams

## 1. Complete System Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AGENT EXECUTION CYCLE                             │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  1. ASSESS CONTEXT                                              │    │
│  │     • Query STM for recent market data                          │    │
│  │     • Check LTM for similar historical contexts                 │    │
│  │     • Calculate volatility, trend, volume                       │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  2. SELECT SOURCES (WITH MEMORY)                                │    │
│  │     • Retrieve recent source performance (STM)                  │    │
│  │     • Query learned patterns from LTM                           │    │
│  │     • Calculate combined scores (70% tech + 30% learning)       │    │
│  │     • Apply context-specific boosts                             │    │
│  │     • Make selection                                            │    │
│  │     ──────────────────────────────────────────────────          │    │
│  │     LOG DECISION: "SOURCE_SELECTION"                            │    │
│  │       Context: market state, cycle, patterns applied            │    │
│  │       Reasoning: scores, selected sources, why                  │    │
│  │       Decision ID: dec_123                                      │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  3. QUERY DATA SOURCES                                          │    │
│  │     For each selected source:                                   │    │
│  │       • Check rate limits (from STM)                            │    │
│  │       • Check circuit breaker state                             │    │
│  │       • Execute query                                           │    │
│  │       • Store result in STM (1h TTL)                            │    │
│  │       ────────────────────────────────────────────              │    │
│  │       LOG DECISION: "QUERY_EXECUTION"                           │    │
│  │         Source: whaleMovements                                  │    │
│  │         Parameters: threshold, timeframe                        │    │
│  │         Parent: dec_123                                         │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  4. GENERATE SIGNALS                                            │    │
│  │     • Analyze query results                                     │    │
│  │     • Apply signal generation rules                             │    │
│  │     • Calculate confidence scores                               │    │
│  │     • Determine target agents                                   │    │
│  │     ──────────────────────────────────────────────────          │    │
│  │     LOG DECISION: "SIGNAL_GENERATION"                           │    │
│  │       Signal type: WHALE_ACTIVITY                               │    │
│  │       Confidence: 0.85                                          │    │
│  │       Reasoning: pattern match + threshold                      │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  5. LOG OUTCOMES                                                │    │
│  │     • Link outcomes to decision IDs                             │    │
│  │     • Record success/failure                                    │    │
│  │     • Calculate quality metrics                                 │    │
│  │     • Update agent learning metrics                             │    │
│  │     ──────────────────────────────────────────────────          │    │
│  │     UPDATE DECISION: dec_123                                    │    │
│  │       Outcome: 2 signals generated, quality 0.85                │    │
│  │       Success: true                                             │    │
│  │       Latency: 1.2s                                             │    │
│  └──────────────────────────┬─────────────────────────────────────┘    │
│                              │                                            │
│                              ▼                                            │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │  6. CONSOLIDATE LEARNING (Periodic)                             │    │
│  │     • Query recent decisions (last 24h)                         │    │
│  │     • Identify patterns with high success rate                  │    │
│  │     • Calculate pattern confidence                              │    │
│  │     • Promote patterns to LTM                                   │    │
│  │     • Update existing pattern confidences                       │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Memory Read Flow

```
Agent needs to make decision
         │
         ▼
    ┌─────────┐
    │ Check   │ ──────────────────────────┐
    │  STM    │ Redis lookup (< 1ms)      │
    └────┬────┘                            │
         │                                 │
    Cache hit?                             │
    │         │                            │
    YES       NO                           │
    │         │                            │
    │         ▼                            │
    │    ┌─────────┐                      │
    │    │ Check   │ DynamoDB query       │
    │    │  LTM    │ (10-50ms)            │
    │    └────┬────┘                      │
    │         │                            │
    │    Found?                            │
    │    │    │                            │
    │   YES   NO                           │
    │    │    │                            │
    │    │    ▼                            │
    │    │  Return                         │
    │    │  default                        │
    │    │                                 │
    │    ▼                                 │
    │  Store in ◄────────────────────────┘
    │  STM for
    │  future hits
    │    │
    ▼    ▼
  Use memory
  in decision
```

## 3. Memory Write Flow

```
Decision made / Data available
         │
         ▼
    ┌─────────┐
    │ Write   │ Redis SET (< 1ms)
    │  to     │ with TTL
    │  STM    │
    └────┬────┘
         │
         ▼
    High value         ┌──────────────────┐
    or persistent? ───→│  Write to LTM    │
    │         │        │  (DynamoDB)      │
    YES       NO       │  Async           │
    │         │        └──────────────────┘
    │         │
    │         ▼
    │    Done (STM only)
    │
    ▼
┌─────────────┐
│ Write to    │ DynamoDB PutItem
│ DynamoDB    │ (10-50ms)
└────┬────────┘
     │
     ▼
Done (STM + LTM)
```

## 4. Decision Logging Flow - Detailed

```
┌──────────────────────────────────────────────────────────────┐
│ BEFORE DECISION                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Gather Context                                           │
│     ├─ Market state (volatility, trend, volume)              │
│     ├─ Agent state (cycle, exploration rate)                 │
│     ├─ Recent memory (STM queries)                           │
│     └─ Applied patterns (LTM patterns)                       │
│                                                               │
│  2. Create Decision Record                                   │
│     decision = {                                             │
│       "decision_id": generate_uuid(),                        │
│       "timestamp": now,                                      │
│       "decision_type": "SOURCE_SELECTION",                   │
│       "context": gathered_context,                           │
│       "reasoning": {},  # To be filled                       │
│       "outcome": None   # To be filled later                 │
│     }                                                         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ MAKE DECISION                                                 │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  3. Execute Decision Logic                                   │
│     ├─ Calculate scores                                      │
│     ├─ Apply memory influence                                │
│     ├─ Apply pattern boosts                                  │
│     ├─ Handle exploration                                    │
│     └─ Make selection                                        │
│                                                               │
│  4. Add Reasoning to Record                                  │
│     decision["reasoning"] = {                                │
│       "scores": calculated_scores,                           │
│       "selected": selected_sources,                          │
│       "memory_influenced": True,                             │
│       "patterns_applied": pattern_ids,                       │
│       "exploration": exploration_triggered                   │
│     }                                                         │
│                                                               │
│  5. Write Decision to Database                               │
│     await decision_logger.log_decision(decision)             │
│     ├─ DynamoDB: agent_decisions table                       │
│     ├─ Redis: decision_chain list                            │
│     └─ Return: decision_id                                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ EXECUTE DECISION                                              │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  6. Perform Actions                                          │
│     ├─ Query selected sources                                │
│     ├─ Generate signals                                      │
│     ├─ Update metrics                                        │
│     └─ Collect outcomes                                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│ AFTER DECISION                                                │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  7. Log Outcome                                              │
│     outcome = {                                              │
│       "success": signals_generated > 0,                      │
│       "signals_generated": 2,                                │
│       "quality_score": 0.85,                                 │
│       "latency_ms": 1200,                                    │
│       "errors": []                                           │
│     }                                                         │
│                                                               │
│  8. Update Decision Record                                   │
│     await decision_logger.log_outcome(                       │
│       decision_id,                                           │
│       outcome                                                │
│     )                                                         │
│     ├─ DynamoDB: Update item with outcome                    │
│     ├─ Calculate success metrics                             │
│     └─ Trigger learning if needed                            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## 5. Pattern Learning Flow

```
┌─────────────────────────────────────────────────────────────┐
│ CONSOLIDATION JOB (Every 6 hours)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Query Recent  │
                    │ Decisions     │
                    │ (last 24h)    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Group By      │
                    │ Context       │
                    │ • Volatility  │
                    │ • Trend       │
                    │ • Hour        │
                    └───────┬───────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │ Analyze Each Group      │
              │ • Success rate          │
              │ • Quality scores        │
              │ • Common sources        │
              │ • Timing patterns       │
              └─────────┬───────────────┘
                        │
                        ▼
          ┌─────────────────────────────────┐
          │ Identify Patterns               │
          │                                 │
          │ IF success_rate > 70% AND       │
          │    occurrences >= 5 AND         │
          │    quality_avg > 0.7            │
          │ THEN create pattern             │
          └─────────┬───────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │ Calculate Pattern Confidence          │
    │                                       │
    │ confidence = (                        │
    │   0.4 * success_rate +                │
    │   0.3 * quality_score +               │
    │   0.2 * sample_size_norm +            │
    │   0.1 * recency_bonus                 │
    │ )                                     │
    └───────────┬───────────────────────────┘
                │
                ▼
    ┌───────────────────────────────────────┐
    │ Store Pattern in LTM                  │
    │                                       │
    │ pattern = {                           │
    │   "pattern_id": generate_id(),        │
    │   "type": "context_source_combo",     │
    │   "context": {"volatility": "high"},  │
    │   "sources": ["whaleMovements"],      │
    │   "confidence": 0.85,                 │
    │   "success_rate": 0.78,               │
    │   "sample_size": 15                   │
    │ }                                     │
    │                                       │
    │ await memory.store_ltm(pattern)       │
    └───────────────────────────────────────┘
```

## 6. Multi-Agent Memory Sharing (Future)

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED MEMORY POOL                        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Market       │  │ Risk         │  │ Trading      │     │
│  │ Hunter       │  │ Manager      │  │ Executor     │     │
│  │ Agent        │  │ Agent        │  │ Agent        │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │             │
│         │    Write         │    Read          │             │
│         │    decisions     │    risk signals  │             │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                │
│                            ▼                                │
│              ┌──────────────────────────┐                  │
│              │  Agent Communication     │                  │
│              │  Memory Space            │                  │
│              │  ┌────────────────────┐  │                  │
│              │  │ Market Hunter says:│  │                  │
│              │  │ "WHALE_ACTIVITY"   │  │                  │
│              │  │ confidence: 0.85   │  │                  │
│              │  └────────────────────┘  │                  │
│              │  ┌────────────────────┐  │                  │
│              │  │ Risk Manager says: │  │                  │
│              │  │ "HIGH_RISK_ALERT"  │  │                  │
│              │  │ action: "REDUCE"   │  │                  │
│              │  └────────────────────┘  │                  │
│              └──────────────────────────┘                  │
│                                                             │
│  Each agent:                                               │
│  • Writes its own decisions to shared space                │
│  • Reads other agents' signals                             │
│  • Learns from collective outcomes                         │
│  • Respects agent-specific privacy settings                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 7. Query Patterns

### Pattern A: Get Recent Context
```
Agent → Memory Manager
  ├─ "Get STM: recent_context"
  └─ Redis: GET stm:market-hunter:context:current
      └─ Returns: {volatility: "high", trend: "bullish"}
```

### Pattern B: Get Historical Pattern
```
Agent → Memory Manager
  ├─ "Get LTM patterns for high_volatility"
  └─ DynamoDB: Query agent_memory_ltm
      WHERE PK = "market-hunter#PATTERN"
      AND confidence > 0.7
      └─ Returns: 5 patterns
```

### Pattern C: Log Decision with Outcome
```
Agent → Decision Logger
  ├─ 1. log_decision(type, context, reasoning)
  │   └─ DynamoDB: PutItem to agent_decisions
  │       └─ Returns: decision_id
  │
  ├─ ... (execute decision) ...
  │
  └─ 2. log_outcome(decision_id, outcome)
      └─ DynamoDB: UpdateItem agent_decisions
          SET outcome = {success: true, ...}
```

### Pattern D: Hierarchical Retrieval
```
Memory Manager receives request
  │
  ├─ 1. Check Redis (STM) - < 1ms
  │   └─ Hit? Return immediately
  │
  ├─ 2. Check DynamoDB hot partition (< 24h) - 10ms
  │   └─ Hit? Cache in Redis + return
  │
  ├─ 3. Check DynamoDB (1-30 days) - 50ms
  │   └─ Hit? Cache in Redis + return
  │
  └─ 4. Check S3 (archive) - 100-500ms
      └─ Hit? Cache in Redis + return
```

## 8. Cost Flow

```
OPERATION                    COST        FREQUENCY/MONTH    MONTHLY
────────────────────────────────────────────────────────────────────
STM Write (Redis)            Free*       ~500K              $0
STM Read (Redis)             Free*       ~1M                $0
LTM Write (DynamoDB)         $1.25/M     26K                $0.03
LTM Read (DynamoDB)          $0.25/M     100K               $0.03
Decision Log Write           $1.25/M     26K                $0.03
Decision Log Read            $0.25/M     50K                $0.01
S3 Storage                   $0.023/GB   1 GB               $0.02
Redis Instance               Hourly      720h               $12.00
────────────────────────────────────────────────────────────────────
TOTAL                                                       ~$12.12

* Redis operations included in instance cost
```

---

This completes the data flow visualization. The diagrams show:
1. Complete system flow from decision to learning
2. Memory read/write patterns
3. Decision logging lifecycle
4. Pattern learning process
5. Future multi-agent architecture
6. Common query patterns
7. Cost breakdown

Ready to discuss and move to implementation! 🚀
