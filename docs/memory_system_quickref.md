# Agent Memory System - Quick Reference

## System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         AGENT LAYER                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Market Hunter Agent (Memory-Aware)                        │  │
│  │  • Makes decisions with memory context                     │  │
│  │  • Logs every decision + reasoning                         │  │
│  │  • Learns from historical patterns                         │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────┬────────────────────────┬────────────────────────┘
                 │                        │
        ┌────────▼─────────┐     ┌───────▼────────┐
        │ Decision Logger  │     │ Memory Manager │
        │ • Log decisions  │     │ • STM (Redis)  │
        │ • Track outcomes │     │ • LTM (DDB)    │
        │ • Query history  │     │ • Hierarchical │
        └────────┬─────────┘     └───────┬────────┘
                 │                        │
                 └────────────┬───────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────┐
│                      STORAGE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ ElastiCache  │  │  DynamoDB    │  │  S3               │   │
│  │  (Redis)     │  │  • Decisions │  │  • Archives       │   │
│  │  • Context   │  │  • Patterns  │  │  • Compliance     │   │
│  │  • Recent    │  │  • State     │  │  • Cold storage   │   │
│  │  • Cache     │  └──────────────┘  └───────────────────┘   │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Hierarchy

```
TIME SCALE              STORAGE           TTL          USE CASE
─────────────────────────────────────────────────────────────────
Immediate (< 1 hour)    Redis            1 hour       Current context, active signals
Recent (1-24 hours)     Redis + DDB      24 hours     Recent performance, quick retrieval  
Historical (1-30 days)  DynamoDB         90 days      Pattern learning, analysis
Archive (> 30 days)     S3               Years        Compliance, deep analysis
```

## Decision Logging Flow

```
1. DECISION MADE
   ↓
   ├─→ Capture Context (market, cycle, state)
   ├─→ Capture Reasoning (scores, selections, why)
   ├─→ Generate Decision ID
   └─→ Write to DynamoDB
   
2. ACTION EXECUTED
   ↓
   ├─→ Capture Outcome (success, metrics, signals)
   ├─→ Link to Decision ID
   └─→ Update DynamoDB
   
3. LEARNING
   ↓
   ├─→ Query Recent Decisions
   ├─→ Identify Patterns
   ├─→ Calculate Confidence
   └─→ Store in LTM
```

## Components to Build

### Phase 1: Foundation
```
src/memory/
├── __init__.py
├── aws_clients.py              # DynamoDB, Redis, S3 clients
├── memory_manager.py           # Hierarchical memory management
└── schemas.py                  # Data models
```

### Phase 2: Decision Logging
```
src/memory/
├── decision_logger.py          # Log all decisions
├── decision_types.py           # Decision type enums
└── query_builder.py            # DynamoDB query helpers
```

### Phase 3: Agent Integration
```
src/
├── memory_aware_agent.py       # Enhanced agent with memory
└── pattern_learner.py          # Pattern identification
```

### Phase 4: Analytics
```
src/memory/
├── analytics.py                # Performance analytics
└── visualization.py            # Dashboard data
```

## Key Decisions Needed

### 1. Storage Strategy
- **Option A**: Redis (ElastiCache) for STM
  - ✅ Faster (sub-millisecond)
  - ❌ More complex (2 services)
  - **Cost**: ~$12/month (t3.micro)

- **Option B**: DynamoDB DAX for STM
  - ✅ Simpler (1 service)
  - ❌ Slightly slower
  - **Cost**: ~$40/month (t3.small)

**Recommendation**: Start with Redis, proven for caching

### 2. Consolidation Strategy
- **Option A**: Automated (EventBridge every 6 hours)
  - ✅ Consistent, reliable
  - ❌ May consolidate incomplete patterns

- **Option B**: Agent-triggered (after N cycles)
  - ✅ More control
  - ❌ May miss consolidation if agent crashes

**Recommendation**: Hybrid - scheduled + agent-triggered

### 3. MVP Scope
- **Option A**: Full system (STM + LTM + Analytics)
  - ✅ Complete feature set
  - ❌ 4-5 weeks development

- **Option B**: Decision logging only
  - ✅ 1-2 weeks, immediate value
  - ❌ No memory benefits yet

**Recommendation**: Phased - logging first, then memory

## Implementation Checklist

### Week 1: Foundation
- [ ] Create `src/memory/` directory structure
- [ ] Implement `aws_clients.py` with DynamoDB/Redis clients
- [ ] Create DynamoDB table schemas
- [ ] Set up ElastiCache Redis (dev environment)
- [ ] Write data models (`schemas.py`)
- [ ] Basic unit tests

### Week 2: Decision Logging
- [ ] Implement `DecisionLogger` class
- [ ] Add decision types enum
- [ ] Create DynamoDB query helpers
- [ ] Integrate logging into `IntegratedMarketHunterAgent`
- [ ] Log source selection decisions
- [ ] Log query decisions
- [ ] Log signal generation decisions
- [ ] Write integration tests

### Week 3: Memory System
- [ ] Implement `MemoryManager` STM functions
- [ ] Implement LTM storage functions
- [ ] Create pattern identification logic
- [ ] Build consolidation job
- [ ] Hierarchical retrieval functions
- [ ] Memory analytics queries

### Week 4: Agent Enhancement
- [ ] Create `MemoryAwareMarketHunterAgent`
- [ ] Integrate memory into source selection
- [ ] Add pattern-based decision enhancement
- [ ] Implement learning from outcomes
- [ ] Create performance analytics
- [ ] Dashboard data preparation

### Week 5: Production
- [ ] Deploy DynamoDB tables (prod)
- [ ] Deploy ElastiCache cluster (prod)
- [ ] Configure IAM roles
- [ ] Set up CloudWatch monitoring
- [ ] Create operational runbooks
- [ ] Load testing
- [ ] Documentation

## Cost Breakdown

```
Service                 Size              Monthly Cost
─────────────────────────────────────────────────────────
ElastiCache Redis       t3.micro (0.5GB)  $12.00
DynamoDB (On-Demand)    26K writes/month  $7.00
DynamoDB (On-Demand)    100K reads/month  $3.00
S3 Storage              1 GB archives     $0.02
CloudWatch Logs         5 GB/month        $2.50
Data Transfer           Minimal           $1.00
────────────────────────────────────────────────────────
TOTAL                                     ~$25.50/month
```

## Questions for Discussion

1. **Storage**: Redis (ElastiCache) vs DynamoDB DAX for short-term memory?
2. **Scope**: Full system or start with just decision logging?
3. **Patterns**: What specific patterns should the agent learn first?
4. **Budget**: Is $25-30/month acceptable for memory system?
5. **Multi-agent**: Design for single agent or multi-agent from day 1?
6. **Consolidation**: How often should we consolidate STM → LTM?
7. **Retention**: 90 days for decisions or longer?
8. **Analytics**: What reports/dashboards are most valuable?

## Sample Decision Log Entry

```json
{
  "decision_id": "dec_2025-10-18_142_source_sel",
  "agent_id": "market-hunter",
  "timestamp": "2025-10-18T14:30:00Z",
  "decision_type": "SOURCE_SELECTION",
  "context": {
    "market": {
      "price": 63500,
      "volatility": "high",
      "trend": "bullish",
      "volume_ratio": 1.5
    },
    "cycle": 142,
    "trading_hours": "american"
  },
  "reasoning": {
    "scores": {
      "whaleMovements": 0.92,
      "derivatives": 0.87,
      "institutional": 0.83
    },
    "selected": ["whaleMovements", "derivatives", "institutional"],
    "exploration": false,
    "memory_influenced": true,
    "patterns_applied": ["whale_pump_correlation"]
  },
  "outcome": {
    "success": true,
    "signals_generated": 2,
    "quality_score": 0.85,
    "latency_ms": 1200,
    "sources_succeeded": 3
  },
  "ttl": 1742310000
}
```

## Next Actions

After discussing the above questions, we will:

1. ✅ Finalize architecture decisions
2. ✅ Choose storage strategy (Redis vs DAX)
3. ✅ Define MVP scope (logging vs full system)
4. ✅ Set budget and cost limits
5. 🚀 Start implementing Phase 1

**Ready to discuss? Let me know your preferences!** 🎯
