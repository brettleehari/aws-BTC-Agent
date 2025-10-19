# Agent Memory and Decision Logging System - Design Discussion

## Overview

Design document for implementing hierarchical memory (short-term and long-term) and comprehensive decision logging for AWS Bedrock-based AI agents, specifically the Market Hunter Agent and future agents in the BTC trading ecosystem.

---

## 1. Requirements Analysis

### 1.1 Core Requirements

Based on project requirements, we need to:
- ✅ **Integrate with databases** (requirement: "integrates APIs, databases, external tools")
- ✅ **Support autonomous decision-making** with traceable reasoning
- ✅ **Use AWS services** for infrastructure
- ✅ **Enable agent learning** from historical decisions

### 1.2 Functional Requirements

**Memory System:**
- **Short-term memory**: Recent context, current cycle data, active market conditions
- **Long-term memory**: Historical patterns, learned strategies, performance metrics
- **Hierarchical structure**: Ability to retrieve at different time scales and relevance levels

**Decision Logging:**
- **Every decision** made by agents must be logged
- **Context capture**: Why the decision was made
- **Outcome tracking**: What happened after the decision
- **Performance analysis**: Success/failure rates, pattern recognition

---

## 2. Architecture Design

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Market Hunter Agent                          │
│  (Decision-making, Learning, Signal Generation)                  │
└───────┬─────────────────────────────────┬───────────────────────┘
        │                                 │
        │ Log decisions                   │ Query memory
        │                                 │
        ▼                                 ▼
┌─────────────────────┐         ┌──────────────────────┐
│  Decision Logger    │         │  Memory Manager      │
│  - Capture context  │         │  - Short-term cache  │
│  - Track outcomes   │         │  - Long-term store   │
│  - Link to memory   │         │  - Hierarchical      │
└──────────┬──────────┘         └──────────┬───────────┘
           │                               │
           │                               │
           ▼                               ▼
┌──────────────────────────────────────────────────────┐
│              AWS Storage Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ DynamoDB    │  │ ElastiCache  │  │ S3          │ │
│  │ (Decisions) │  │ (Short-term) │  │ (Archives)  │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
└──────────────────────────────────────────────────────┘
```

### 2.2 Component Breakdown

#### **A. Memory Manager**

Handles hierarchical memory with different time scales:

**Short-Term Memory (STM):**
- **Retention**: Last 1-24 hours
- **Storage**: ElastiCache Redis / In-memory Python cache
- **Contents**:
  - Current market context (volatility, trend, volume)
  - Recent source queries (last 10 cycles)
  - Active signals being monitored
  - Real-time rate limit tracking
  - Current agent state (exploration vs exploitation)
  
**Long-Term Memory (LTM):**
- **Retention**: Days to months (configurable)
- **Storage**: DynamoDB with TTL / S3 for archives
- **Contents**:
  - Historical source performance by context
  - Learned patterns (e.g., "whale movements predict pumps 70% of the time in bullish trends")
  - Strategy effectiveness over time
  - Market condition archetypes
  - Agent configuration evolution

**Hierarchical Retrieval:**
```
Level 1: Immediate (< 1 hour)   → ElastiCache
Level 2: Recent (1-24 hours)    → DynamoDB hot partition
Level 3: Historical (1-30 days) → DynamoDB
Level 4: Archive (> 30 days)    → S3 with indexing
```

#### **B. Decision Logger**

Captures every agent decision with full context:

**Decision Types:**
1. **Source Selection Decisions**
   - Which sources to query
   - Why those sources (scoring breakdown)
   - Context at time of decision
   
2. **Query Decisions**
   - What parameters to use
   - Priority level chosen
   - Fallback strategy
   
3. **Signal Generation Decisions**
   - Why a signal was generated
   - Confidence calculation
   - Target agents/actions
   
4. **Learning Decisions**
   - Metric updates
   - Exploration vs exploitation choice
   - Strategy adjustments

**Logged Attributes:**
```python
{
    "decision_id": "uuid",
    "agent_id": "market-hunter",
    "timestamp": "ISO8601",
    "decision_type": "SOURCE_SELECTION",
    "context": {
        "market": {"volatility": "high", "trend": "bullish"},
        "cycle": 142,
        "trading_hours": "american"
    },
    "reasoning": {
        "scores": {"whaleMovements": 0.92, "derivatives": 0.87},
        "selected": ["whaleMovements", "derivatives", "institutional"],
        "exploration_triggered": false
    },
    "outcome": {
        "success": true,
        "signals_generated": 2,
        "quality_score": 0.85,
        "latency_ms": 1200
    },
    "metadata": {
        "version": "1.0",
        "experiment_id": null
    }
}
```

---

## 3. Storage Strategy

### 3.1 Storage Selection Matrix

| Data Type | Volume | Access Pattern | Retention | AWS Service | Reasoning |
|-----------|--------|----------------|-----------|-------------|-----------|
| **Short-term memory** | Low (MB) | Very frequent reads/writes | 1-24 hours | **ElastiCache Redis** | Sub-millisecond latency, in-memory |
| **Decision logs** | High (GB/month) | Write-heavy, range queries | 90 days hot, archive after | **DynamoDB** | Scalable NoSQL, TTL support, fast queries |
| **Long-term patterns** | Medium (100s MB) | Read-heavy, analytical | Indefinite | **DynamoDB + S3** | DynamoDB for active, S3 for historical |
| **Raw data archives** | High (TB potential) | Rare access, compliance | Years | **S3 Glacier** | Cost-effective archival |
| **Agent state** | Small (KB) | Frequent updates | Session-based | **ElastiCache + DynamoDB** | Fast state access, persistent backup |

### 3.2 DynamoDB Table Design

**Table 1: `agent_decisions`**

```python
Primary Key: 
  - PK: agent_id#decision_type  (e.g., "market-hunter#SOURCE_SELECTION")
  - SK: timestamp#decision_id   (e.g., "2025-10-18T10:30:00Z#uuid")

Attributes:
  - decision_id (String, UUID)
  - agent_id (String)
  - decision_type (String)
  - timestamp (Number, Unix timestamp)
  - iso_timestamp (String)
  - context (Map)
  - reasoning (Map)
  - outcome (Map)
  - success (Boolean)
  - ttl (Number, for auto-expiration)

GSI 1 - Query by outcome:
  - PK: agent_id#success
  - SK: timestamp

GSI 2 - Query by market context:
  - PK: agent_id#context_type
  - SK: timestamp
```

**Table 2: `agent_memory_ltm`**

```python
Primary Key:
  - PK: agent_id#memory_type  (e.g., "market-hunter#PATTERN")
  - SK: pattern_id            (e.g., "whale_pump_correlation")

Attributes:
  - pattern_id (String)
  - agent_id (String)
  - memory_type (String: PATTERN, STRATEGY, ARCHETYPE)
  - learned_at (Number, timestamp)
  - confidence (Number, 0.0-1.0)
  - data (Map, flexible schema)
  - access_count (Number)
  - last_accessed (Number)
  - success_rate (Number)
  - version (Number)

GSI 1 - Query by confidence:
  - PK: agent_id#memory_type
  - SK: confidence (descending)
```

**Table 3: `agent_state`**

```python
Primary Key:
  - PK: agent_id
  - SK: state_type  (e.g., "CURRENT", "CHECKPOINT")

Attributes:
  - agent_id (String)
  - state_type (String)
  - current_cycle (Number)
  - source_metrics (Map)
  - context_performance (Map)
  - configuration (Map)
  - last_updated (Number)
  - version (Number)
```

### 3.3 ElastiCache Redis Structure

**Short-Term Memory Keys:**

```python
# Current market context (1 hour TTL)
"stm:{agent_id}:context:current" → JSON

# Recent queries (24 hour TTL)
"stm:{agent_id}:queries:recent" → List of query results

# Active signals (4 hour TTL)
"stm:{agent_id}:signals:active" → Sorted Set by timestamp

# Rate limit tracking (5 minute TTL)
"stm:{agent_id}:ratelimit:{source_id}" → Counter

# Source performance cache (15 minute TTL)
"stm:{agent_id}:performance:{source}:{context}" → JSON

# Decision chain (links recent decisions, 2 hour TTL)
"stm:{agent_id}:decision_chain" → List of decision_ids
```

---

## 4. Implementation Components

### 4.1 Core Components to Build

#### **Component 1: Memory Manager** (`src/memory/memory_manager.py`)

```python
class MemoryManager:
    """
    Manages hierarchical agent memory
    """
    def __init__(self, agent_id, redis_client, dynamodb_client):
        pass
    
    # Short-term memory
    async def store_stm(self, key, data, ttl_seconds)
    async def retrieve_stm(self, key)
    async def clear_stm(self, pattern=None)
    
    # Long-term memory
    async def store_ltm(self, memory_type, pattern_id, data)
    async def retrieve_ltm(self, memory_type, filters)
    async def update_ltm_confidence(self, pattern_id, new_confidence)
    
    # Hierarchical retrieval
    async def get_context_memory(self, time_range, context_filter)
    async def get_pattern_memory(self, pattern_type, min_confidence)
    
    # Memory consolidation
    async def consolidate_to_ltm(self, stm_key, pattern_type)
```

#### **Component 2: Decision Logger** (`src/memory/decision_logger.py`)

```python
class DecisionLogger:
    """
    Logs all agent decisions with context and outcomes
    """
    def __init__(self, agent_id, dynamodb_client, memory_manager):
        pass
    
    async def log_decision(
        self,
        decision_type,
        context,
        reasoning,
        metadata=None
    ) -> str:  # Returns decision_id
        pass
    
    async def log_outcome(
        self,
        decision_id,
        outcome,
        success,
        metrics=None
    ):
        pass
    
    async def query_decisions(
        self,
        decision_type=None,
        time_range=None,
        success_filter=None,
        context_filter=None,
        limit=100
    ):
        pass
    
    async def get_decision_chain(self, decision_id, depth=5):
        """Get related decisions (before/after)"""
        pass
    
    async def analyze_decision_patterns(
        self,
        decision_type,
        time_range,
        group_by="context"
    ):
        """Aggregate decision outcomes for learning"""
        pass
```

#### **Component 3: Memory-Aware Agent** (Enhanced `IntegratedMarketHunterAgent`)

```python
class MemoryAwareMarketHunterAgent(IntegratedMarketHunterAgent):
    """
    Extended agent with memory and decision logging
    """
    def __init__(self, ..., memory_manager, decision_logger):
        super().__init__(...)
        self.memory = memory_manager
        self.logger = decision_logger
    
    async def select_sources_with_memory(self, context, max_sources):
        """
        Source selection enhanced with memory:
        1. Check short-term memory for recent performance
        2. Query long-term memory for patterns
        3. Make decision with full context
        4. Log decision and reasoning
        """
        # Retrieve recent performance from STM
        recent_perf = await self.memory.retrieve_stm(
            f"performance:{context.value}"
        )
        
        # Query LTM for learned patterns
        patterns = await self.memory.retrieve_ltm(
            memory_type="PATTERN",
            filters={"context": context.value, "min_confidence": 0.7}
        )
        
        # Make decision (existing logic + memory)
        selected = self.select_sources(context, max_sources)
        
        # Log decision
        decision_id = await self.logger.log_decision(
            decision_type="SOURCE_SELECTION",
            context={
                "market": context.value,
                "cycle": self.current_cycle,
                "recent_performance": recent_perf,
                "applied_patterns": [p["pattern_id"] for p in patterns]
            },
            reasoning={
                "scores": scores,
                "selected": selected,
                "patterns_influenced": True
            }
        )
        
        return selected, decision_id
    
    async def learn_from_outcomes(self):
        """
        Consolidate recent decisions into long-term patterns
        """
        # Query recent decisions
        recent = await self.logger.query_decisions(
            time_range=(now - 24h, now),
            success_filter=True
        )
        
        # Identify patterns
        patterns = self._identify_patterns(recent)
        
        # Store in LTM
        for pattern in patterns:
            await self.memory.store_ltm(
                memory_type="PATTERN",
                pattern_id=pattern["id"],
                data=pattern
            )
```

#### **Component 4: AWS Infrastructure Helper** (`src/memory/aws_clients.py`)

```python
class AWSMemoryClients:
    """
    Manages AWS client connections for memory system
    """
    @staticmethod
    def get_dynamodb_client(region="us-east-1"):
        """Get DynamoDB client"""
        pass
    
    @staticmethod
    def get_redis_client(cluster_endpoint):
        """Get ElastiCache Redis client"""
        pass
    
    @staticmethod
    def get_s3_client(region="us-east-1"):
        """Get S3 client for archives"""
        pass
    
    @staticmethod
    def create_tables_if_not_exist():
        """Initialize DynamoDB tables"""
        pass
    
    @staticmethod
    def create_redis_cache_if_not_exist():
        """Initialize ElastiCache cluster"""
        pass
```

#### **Component 5: Memory Analytics** (`src/memory/analytics.py`)

```python
class MemoryAnalytics:
    """
    Analytics and insights from memory and decision logs
    """
    def __init__(self, decision_logger, memory_manager):
        pass
    
    async def get_success_rate_by_context(self, time_range):
        """Analyze success rates across different market contexts"""
        pass
    
    async def get_source_effectiveness(self, time_range):
        """Which sources contribute to successful signals?"""
        pass
    
    async def get_pattern_confidence_trend(self, pattern_id):
        """How has confidence in a pattern changed over time?"""
        pass
    
    async def identify_emerging_patterns(self, min_occurrences=5):
        """Find new patterns worth promoting to LTM"""
        pass
    
    async def generate_performance_report(self, time_range):
        """Comprehensive performance report"""
        pass
```

---

## 5. Integration with Existing System

### 5.1 Minimal Changes to Existing Code

**Current Agent → Memory-Aware Agent:**

```python
# Before (current implementation)
agent = IntegratedMarketHunterAgent(
    agent_name="market-hunter",
    learning_rate=0.1
)

# After (with memory)
from src.memory import MemoryManager, DecisionLogger

memory_manager = MemoryManager(
    agent_id="market-hunter",
    redis_endpoint=os.environ["REDIS_ENDPOINT"],
    dynamodb_table_prefix="btc-agent"
)

decision_logger = DecisionLogger(
    agent_id="market-hunter",
    memory_manager=memory_manager
)

agent = MemoryAwareMarketHunterAgent(
    agent_name="market-hunter",
    learning_rate=0.1,
    memory_manager=memory_manager,
    decision_logger=decision_logger
)
```

### 5.2 Backward Compatibility

- Existing `IntegratedMarketHunterAgent` continues to work without memory
- Memory features are **additive** - not breaking changes
- Can enable memory gradually (start with logging, then add STM, then LTM)

---

## 6. Usage Patterns

### 6.1 Pattern 1: Query with Memory Context

```python
async def run_cycle_with_memory(self, market_data):
    # 1. Check short-term memory for recent similar contexts
    similar_contexts = await self.memory.get_context_memory(
        time_range=(now - 1hour, now),
        context_filter={"volatility": "high"}
    )
    
    # 2. Select sources with memory influence
    selected, decision_id = await self.select_sources_with_memory(
        context, max_sources=6
    )
    
    # 3. Query sources
    results = []
    for source in selected:
        result = await self.query_source(source)
        results.append(result)
        
        # Store in STM for fast retrieval
        await self.memory.store_stm(
            f"queries:{source}:latest",
            result,
            ttl_seconds=3600
        )
    
    # 4. Generate signals with logged reasoning
    signals = self._generate_signals(results, context)
    
    # 5. Log outcome
    await self.logger.log_outcome(
        decision_id=decision_id,
        outcome={"signals": signals, "sources_used": len(results)},
        success=len(signals) > 0,
        metrics={"quality": self._calculate_quality(signals)}
    )
    
    return signals
```

### 6.2 Pattern 2: Learning from History

```python
async def consolidate_learnings(self):
    """
    Nightly job to consolidate STM → LTM
    """
    # 1. Analyze last 24h of decisions
    decisions = await self.logger.query_decisions(
        time_range=(now - 24h, now)
    )
    
    # 2. Calculate success patterns
    analytics = MemoryAnalytics(self.logger, self.memory)
    patterns = await analytics.identify_emerging_patterns(
        min_occurrences=5
    )
    
    # 3. Promote patterns to LTM
    for pattern in patterns:
        await self.memory.store_ltm(
            memory_type="PATTERN",
            pattern_id=pattern["id"],
            data={
                "description": pattern["description"],
                "confidence": pattern["confidence"],
                "success_rate": pattern["success_rate"],
                "sample_size": pattern["occurrences"],
                "learned_at": now
            }
        )
    
    # 4. Update existing pattern confidences
    for pattern_id, new_confidence in pattern_updates:
        await self.memory.update_ltm_confidence(
            pattern_id, new_confidence
        )
```

### 6.3 Pattern 3: Decision Auditing

```python
async def audit_decision_chain(decision_id):
    """
    Trace a decision and its consequences
    """
    logger = DecisionLogger(agent_id="market-hunter")
    
    # Get the decision
    decision = await logger.get_decision(decision_id)
    
    # Get related decisions (what led to this, what came after)
    chain = await logger.get_decision_chain(decision_id, depth=10)
    
    # Analyze the chain
    print(f"Decision: {decision['decision_type']}")
    print(f"Context: {decision['context']}")
    print(f"Reasoning: {decision['reasoning']}")
    print(f"Outcome: {decision['outcome']}")
    print(f"\nRelated decisions: {len(chain)}")
    
    for related in chain:
        print(f"  - {related['decision_type']} at {related['timestamp']}")
```

---

## 7. Cost Estimation

### 7.1 AWS Service Costs (Estimated Monthly)

**Scenario: Market Hunter Agent running every 10 minutes**
- 144 cycles/day = 4,320 cycles/month
- ~6 decisions per cycle = 25,920 decisions/month

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **DynamoDB** | 26K writes, 100K reads | $5-10 |
| **ElastiCache (cache.t3.micro)** | 1 node, 0.5 GB | $12 |
| **S3 Storage** | 1 GB/month archives | $0.02 |
| **Data Transfer** | Minimal within region | $1-2 |
| **CloudWatch Logs** | 5 GB/month | $2.50 |
| **Total** | | **~$20-25/month** |

### 7.2 Cost Optimization Strategies

1. **Use DynamoDB On-Demand** for variable workloads
2. **TTL on decisions** - auto-delete after 90 days
3. **S3 Intelligent-Tiering** for archives
4. **ElastiCache reserved instances** for production
5. **Batch writes** to reduce DynamoDB costs

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1)
- ✅ Create memory module structure
- ✅ Implement AWS client helpers
- ✅ Create DynamoDB table schemas
- ✅ Set up ElastiCache cluster (dev)
- ✅ Basic MemoryManager with STM

### Phase 2: Decision Logging (Week 2)
- ✅ Implement DecisionLogger
- ✅ Integrate with existing agent
- ✅ Add decision logging to all decision points
- ✅ Create decision query functions
- ✅ Basic testing

### Phase 3: Long-Term Memory (Week 3)
- ✅ Implement LTM storage in DynamoDB
- ✅ Create pattern identification logic
- ✅ Build consolidation jobs (STM → LTM)
- ✅ Add pattern querying to agent
- ✅ Hierarchical retrieval

### Phase 4: Analytics & Learning (Week 4)
- ✅ Implement MemoryAnalytics
- ✅ Build performance dashboards
- ✅ Create learning algorithms
- ✅ Automated pattern promotion
- ✅ Integration tests

### Phase 5: Production & Monitoring (Week 5)
- ✅ Deploy to production AWS account
- ✅ Set up CloudWatch alarms
- ✅ Create operational runbooks
- ✅ Performance tuning
- ✅ Documentation

---

## 9. Monitoring & Observability

### 9.1 Key Metrics

**Memory System:**
- STM hit rate (cache effectiveness)
- LTM pattern confidence distribution
- Memory consolidation success rate
- Storage costs by component

**Decision Logging:**
- Decisions logged per minute
- Decision types distribution
- Average decision latency
- Success rate by decision type

**Agent Performance:**
- Decisions influenced by LTM patterns
- Pattern confidence evolution
- Learning rate (new patterns identified)
- Memory-to-outcome correlation

### 9.2 CloudWatch Dashboards

```python
# Custom metrics to emit
cloudwatch.put_metric_data(
    Namespace='BTCAgent/Memory',
    MetricData=[
        {
            'MetricName': 'STMHitRate',
            'Value': hit_rate,
            'Unit': 'Percent'
        },
        {
            'MetricName': 'DecisionsLogged',
            'Value': decision_count,
            'Unit': 'Count'
        },
        {
            'MetricName': 'PatternConfidence',
            'Value': avg_confidence,
            'Unit': 'None'
        }
    ]
)
```

---

## 10. Security & Compliance

### 10.1 Data Protection

- **Encryption at rest**: DynamoDB encryption enabled
- **Encryption in transit**: TLS for Redis and DynamoDB
- **Access control**: IAM roles with least privilege
- **Audit trail**: CloudTrail for all API calls

### 10.2 Data Retention Policies

```python
RETENTION_POLICY = {
    "short_term_memory": {
        "context": 1_hour,
        "queries": 24_hours,
        "signals": 4_hours,
        "rate_limits": 5_minutes
    },
    "decision_logs": {
        "hot": 90_days,      # DynamoDB
        "archive": 1_year,    # S3
        "compliance": 7_years # S3 Glacier
    },
    "long_term_memory": {
        "patterns": "indefinite",
        "low_confidence": 30_days,  # Auto-prune
        "deprecated": 180_days
    }
}
```

---

## 11. Discussion Questions

Before we start coding, let's discuss:

### 11.1 Architecture Decisions

1. **Storage Choice**: 
   - Should we use ElastiCache Redis or DynamoDB DAX for short-term memory?
   - Trade-off: Redis = faster, DAX = simpler (one service)

2. **Memory Consolidation**:
   - Automated (EventBridge scheduled) or agent-triggered?
   - How often should we consolidate STM → LTM?

3. **Pattern Identification**:
   - Rule-based or ML-based pattern detection?
   - Confidence threshold for promoting to LTM?

### 11.2 Integration Decisions

4. **Backward Compatibility**:
   - Keep separate `MemoryAwareMarketHunterAgent` or enhance existing?
   - Gradual rollout strategy?

5. **Decision Granularity**:
   - Log every micro-decision or just major decisions?
   - Balance between completeness and cost

### 11.3 Operational Decisions

6. **Monitoring**:
   - What CloudWatch alarms are critical?
   - How to alert on memory system degradation?

7. **Cost Management**:
   - Budget limits for memory system?
   - How to auto-scale or throttle if costs spike?

8. **Testing Strategy**:
   - How to test memory persistence across agent restarts?
   - Load testing for 1000s of decisions/minute?

### 11.4 Feature Scope

9. **MVP vs Full System**:
   - Start with just decision logging, or build full hierarchical memory?
   - Which phase should we prioritize?

10. **Multi-Agent Support**:
    - Design for just Market Hunter or all future agents?
    - Shared memory pool or isolated per agent?

---

## 12. Next Steps

Once we align on the above questions, we can proceed with:

1. **Finalize architecture** based on discussion
2. **Create detailed file structure**
3. **Implement Phase 1** (Foundation)
4. **Write comprehensive tests**
5. **Deploy to dev environment**
6. **Iterate based on real performance data**

---

## Questions for Discussion

**Please provide your thoughts on:**

1. Which storage approach do you prefer for short-term memory (Redis vs DAX)?
2. Should memory consolidation be automated or manual?
3. What's our MVP - just logging or full hierarchical memory?
4. Are there specific patterns you want the agent to learn first?
5. What's the acceptable monthly cost for the memory system?
6. Should we support multi-agent shared memory from day 1?

Let's discuss these points before we start implementing! 🚀
