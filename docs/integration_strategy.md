# Integration Strategy: Market Hunter Agent + Data Interfaces Module

## Overview

This document outlines the integration strategy between the **Market Hunter Agent** (autonomous decision-making) and the **Data Interfaces Module** (capability advertisement & rate limiting).

---

## Architecture Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│              Market Hunter Agent                             │
│  (Autonomous Decision Making)                                │
│                                                              │
│  ┌────────────────────────────────────────────────┐         │
│  │  Decision Engine                                │         │
│  │  • Assess market context                        │         │
│  │  • Calculate source priorities                  │         │
│  │  • Learn from results                           │         │
│  └─────────────────┬──────────────────────────────┘         │
│                    │                                         │
│                    │ Query: What sources can provide         │
│                    │        on-chain data with whale         │
│                    │        tracking capability?             │
│                    ▼                                         │
│  ┌────────────────────────────────────────────────┐         │
│  │  Capability Registry (from Data Interfaces)     │         │
│  │  • Discover available sources                   │         │
│  │  • Check rate limits                            │         │
│  │  • Get quality scores                           │         │
│  │  • Filter by capabilities                       │         │
│  └─────────────────┬──────────────────────────────┘         │
│                    │                                         │
│                    │ Returns: [Glassnode (score: 0.95),     │
│                    │          CoinGecko (score: 0.45)]      │
│                    ▼                                         │
│  ┌────────────────────────────────────────────────┐         │
│  │  Data Interface Manager                         │         │
│  │  • Route requests to best source                │         │
│  │  • Handle rate limits                           │         │
│  │  • Automatic fallback                           │         │
│  │  • Circuit breaker protection                   │         │
│  └─────────────────┬──────────────────────────────┘         │
│                    │                                         │
│                    ▼                                         │
│            [Glassnode API]                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Integration Strategy: 3 Approaches

### **Approach 1: Direct Integration (Recommended)**
Replace hardcoded DATA_SOURCES with dynamic capability discovery

**Pros:**
- ✅ Leverages all Data Interfaces features (rate limiting, fallback, caching)
- ✅ Agent learns from real quality scores
- ✅ Automatic adaptation to new sources
- ✅ Production-ready with circuit breakers

**Cons:**
- ⚠️ More complex initial setup
- ⚠️ Agent decisions influenced by technical metrics

---

### **Approach 2: Hybrid (Flexible)**
Agent makes high-level decisions, Data Interfaces handles execution

**Pros:**
- ✅ Agent autonomy preserved
- ✅ Technical reliability from Data Interfaces
- ✅ Best of both worlds

**Cons:**
- ⚠️ Need to map agent's logical sources to technical sources

---

### **Approach 3: Layered (Separation of Concerns)**
Agent calls Data Interfaces through well-defined interface

**Pros:**
- ✅ Clean separation
- ✅ Easy to test
- ✅ Can swap implementations

**Cons:**
- ⚠️ More abstraction layers
- ⚠️ Potential duplication

---

## Recommended: Hybrid Approach

### **Phase 1: Mapping Layer**

Create mapping between agent's logical sources and technical data sources:

```python
# Market Hunter Agent's logical view
LOGICAL_SOURCES = {
    "whaleMovements": {
        "data_types": [DataType.WHALE_TRANSACTIONS, DataType.ON_CHAIN],
        "capabilities": [Capability.WHALE_TRACKING],
        "priority": "high"
    },
    "narrativeShifts": {
        "data_types": [DataType.SOCIAL_SENTIMENT, DataType.NEWS],
        "capabilities": [Capability.SENTIMENT_ANALYSIS],
        "priority": "medium"
    },
    "macroSignals": {
        "data_types": [DataType.SOCIAL_SENTIMENT],
        "capabilities": [Capability.SENTIMENT_ANALYSIS],
        "priority": "medium"
    },
    "institutionalFlows": {
        "data_types": [DataType.EXCHANGE_FLOWS, DataType.ON_CHAIN],
        "capabilities": [Capability.EXCHANGE_MONITORING],
        "priority": "high"
    },
    # ... etc
}
```

### **Phase 2: Enhanced Agent with Integration**

```python
class EnhancedMarketHunterAgent(MarketHunterAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Integrate Data Interfaces
        self.data_manager = get_manager()
        self.data_registry = get_registry()
        
        # Enable reliability features
        self.data_manager.enable_fallback = True
        self.data_manager.cache_ttl = 60
    
    def select_sources(self, context: MarketContext) -> List[str]:
        """
        Agent makes high-level source selection decisions
        """
        # Agent's autonomous decision logic (unchanged)
        selected_logical_sources = super().select_sources(context)
        
        # Map to technical sources with capability awareness
        technical_sources = []
        for logical_source in selected_logical_sources:
            mapping = LOGICAL_SOURCES[logical_source]
            
            # Query registry for capable sources
            candidates = self.data_registry.find_sources(
                data_type=mapping["data_types"][0],
                capabilities=mapping["capabilities"]
            )
            
            # Check rate limits before adding
            for source_name in candidates:
                source = self.data_registry.create_source_instance(source_name)
                rate_status = source.get_rate_limit_status()
                
                if not rate_status.get('rate_limited', False):
                    technical_sources.append({
                        'logical': logical_source,
                        'technical': source_name,
                        'quality_score': self._get_combined_score(
                            logical_source, 
                            source_name
                        )
                    })
        
        return technical_sources
    
    def _get_combined_score(self, logical_source: str, technical_source: str) -> float:
        """
        Combine agent's learned metrics with technical quality scores
        """
        # Agent's historical performance
        agent_score = self.source_metrics[logical_source].success_rate
        
        # Technical quality from Data Interfaces
        metadata = self.data_registry.get_metadata(technical_source)
        technical_score = metadata.reliability_score
        
        # Weighted combination (70% technical, 30% agent learning)
        return 0.7 * technical_score + 0.3 * agent_score
```

---

## Key Integration Features

### **1. Rate Limit Awareness**

```python
async def query_source_with_rate_limit_check(
    self, 
    logical_source: str,
    context: MarketContext
) -> Optional[Dict]:
    """
    Query source with automatic rate limit handling
    """
    mapping = LOGICAL_SOURCES[logical_source]
    
    # Get best available source from registry
    request = DataRequest(
        data_type=mapping["data_types"][0],
        symbol="BTC",
        parameters=self._get_query_params(logical_source, context)
    )
    
    # Manager handles rate limits, fallback, caching automatically
    response = await self.data_manager.fetch(request)
    
    if response.success:
        # Update agent's metrics
        self._record_success(logical_source, response)
        return response.data
    else:
        # Log failure reason (rate limit, circuit breaker, etc.)
        logger.warning(
            f"{logical_source} failed: {response.error_code} - {response.error}"
        )
        self._record_failure(logical_source, response.error_code)
        return None
```

### **2. Capability Discovery**

```python
def discover_available_capabilities(self) -> Dict:
    """
    Agent discovers what it can actually do based on registered sources
    """
    summary = self.data_registry.generate_capability_summary()
    
    # Map to agent's logical sources
    available_logical_sources = []
    for logical_source, mapping in LOGICAL_SOURCES.items():
        # Check if any technical source can fulfill this
        candidates = self.data_registry.find_sources(
            data_type=mapping["data_types"][0],
            capabilities=mapping["capabilities"]
        )
        
        if candidates:
            available_logical_sources.append({
                'name': logical_source,
                'technical_sources': candidates,
                'cost_tier': min(
                    self.data_registry.get_metadata(s).cost_tier.value 
                    for s in candidates
                ),
                'best_response_time': min(
                    self.data_registry.get_metadata(s).response_time.value
                    for s in candidates
                )
            })
    
    return {
        'available_sources': available_logical_sources,
        'total_technical_sources': summary['total_sources'],
        'capabilities': summary['capabilities']
    }
```

### **3. Adaptive Learning Integration**

```python
def update_metrics_with_technical_feedback(
    self,
    logical_source: str,
    technical_source: str,
    response: DataResponse
):
    """
    Update agent's learning with technical performance data
    """
    # Agent's existing learning
    agent_metric = self.source_metrics[logical_source]
    
    # Technical feedback
    technical_feedback = {
        'latency': response.latency_ms,
        'cached': response.cached,
        'source': technical_source,
        'quality': 1.0 if response.success else 0.0
    }
    
    # Combined learning with exponential moving average
    old_success = agent_metric.success_rate
    new_observation = technical_feedback['quality']
    
    agent_metric.success_rate = (
        (1 - self.learning_rate) * old_success + 
        self.learning_rate * new_observation
    )
    
    # Track technical source performance separately
    if not hasattr(self, 'technical_metrics'):
        self.technical_metrics = {}
    
    if technical_source not in self.technical_metrics:
        self.technical_metrics[technical_source] = {
            'calls': 0,
            'successes': 0,
            'avg_latency': 0,
            'cache_hits': 0
        }
    
    metrics = self.technical_metrics[technical_source]
    metrics['calls'] += 1
    if response.success:
        metrics['successes'] += 1
    if response.cached:
        metrics['cache_hits'] += 1
    
    # Update average latency
    n = metrics['calls']
    metrics['avg_latency'] = (
        (metrics['avg_latency'] * (n - 1) + response.latency_ms) / n
    )
```

---

## Implementation Roadmap

### **Step 1: Create Mapping Configuration** ✅
- Define LOGICAL_SOURCES mapping
- Map agent concepts to data types/capabilities

### **Step 2: Enhance MarketHunterAgent** ✅
- Add Data Interfaces initialization
- Integrate capability discovery
- Add rate limit checking

### **Step 3: Modify Source Selection Logic** 
- Replace hardcoded sources with registry queries
- Combine agent learning with technical scores
- Handle rate limit awareness

### **Step 4: Update Query Execution**
- Use DataInterfaceManager.fetch() instead of direct Bedrock calls
- Handle responses with circuit breaker awareness
- Update metrics with technical feedback

### **Step 5: Add Monitoring & Observability**
- Log source selection decisions
- Track rate limit hits
- Monitor circuit breaker states
- Dashboard showing agent + technical metrics

---

## Benefits of Integration

| Feature | Before | After |
|---------|--------|-------|
| **Source Discovery** | Hardcoded 8 sources | Dynamic based on registered sources |
| **Rate Limiting** | Agent unaware | Automatic handling + circuit breakers |
| **Fallback** | None | Automatic alternative source selection |
| **Caching** | None | 60s TTL reduces API calls |
| **Quality Scores** | Agent learning only | Combined: 70% technical + 30% learning |
| **New Sources** | Code changes required | Automatic discovery |
| **Cost Awareness** | None | Source selection considers cost tier |
| **Reliability** | Single point of failure | Multi-source redundancy |

---

## Code Changes Required

### Files to Modify:
1. ✅ `src/market_hunter_agent.py` - Add Data Interfaces integration
2. ✅ Create `src/source_mapping.py` - Logical to technical mapping
3. ✅ Update `src/example_usage.py` - Demo new integration
4. ⏳ Create `src/bedrock_action_handler.py` - Lambda handler with Data Interfaces

### Files to Create:
1. ✅ `examples/integrated_agent.py` - Full integration example
2. ⏳ `config/source_mapping.json` - Configuration file
3. ⏳ `tests/test_integration.py` - Integration tests

---

## Next Steps

**Would you like me to:**
1. ✅ Create the source mapping configuration
2. ✅ Build the enhanced MarketHunterAgent with full integration
3. ✅ Create Lambda handler that uses both components
4. ✅ Build comprehensive integration tests
5. ✅ Create deployment scripts for the integrated system

**Let me know which one you'd like to start with!** 🚀
