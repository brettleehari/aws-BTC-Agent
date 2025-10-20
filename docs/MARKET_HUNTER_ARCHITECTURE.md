# Market Hunter Agent - Architecture & Implementation Guide

## 🎯 Overview

The **Market Hunter Agent** is a hybrid **Adaptive Learning + Goal-Oriented** autonomous agent that intelligently selects and queries data sources to generate actionable Bitcoin market signals.

### Why Hybrid Architecture?

| Component | Purpose | Benefits |
|-----------|---------|----------|
| **Adaptive Learning Core** (Primary) | Learn optimal source selection | • Improves over time<br>• Adapts to market changes<br>• Context-aware decisions |
| **Goal-Oriented Layer** (Secondary) | Achieve specific objectives | • Clear KPIs (signal quality)<br>• Cost optimization<br>• Actionable outputs |

---

## 🏗️ Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────┐
│                    GOAL-ORIENTED LAYER                      │
│  • Signal Generation (Actionable alerts)                    │
│  • Multi-Objective Optimization (Accuracy vs Cost)          │
│  • KPI Tracking (Signal quality, data freshness)            │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│                  ADAPTIVE LEARNING CORE                     │
│  • Source Performance Tracking                              │
│  • Context-Aware Scoring                                    │
│  • Exploration vs Exploitation                              │
│  • Continuous Improvement (Learning Rate: 0.1)              │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCE LAYER                       │
│  7 Integrated Sources + 2 Advanced Modules                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Source Mapping

Our **7 live data sources** map perfectly to Market Hunter's 8 source categories:

| Market Hunter Source | Our Implementation | Data Source | Status |
|---------------------|-------------------|-------------|---------|
| **whaleMovements** | Large BTC transactions | Blockchain.com | ✅ Live |
| **narrativeShifts** | Sentiment trends | NewsAPI + Twitter + Sentiment Analyzer | ✅ Live |
| **influencerSignals** | Social media activity | Twitter (10 influencers) | ✅ Live |
| **technicalBreakouts** | Chart patterns | Technical Indicators (RSI, MACD, BB, SMA, EMA) | ✅ Live |
| **macroSignals** | Market psychology | Fear & Greed Index | ✅ Live |
| **arbitrageOpportunities** | Price spreads | CoinGecko + Binance + Alpha Vantage | ✅ Live |
| **institutionalFlows** | On-chain metrics | Blockchain.com | ✅ Live |
| **derivativesSignals** | Funding rates, OI | *To be added* | ⏳ Planned |

**Coverage**: 7/8 sources (87.5%) ✅

---

## 🧠 Decision-Making Process

Each cycle follows 6 steps:

```
1. ASSESS MARKET CONTEXT
   ├─ Fetch current price (CoinGecko)
   ├─ Calculate volatility (24h price change)
   ├─ Determine trend (bullish/bearish/neutral)
   ├─ Identify trading session (Asian/European/American)
   └─ Assess volume ratio

2. CALCULATE SOURCE SCORES
   ├─ Base score (success rate + signal quality)
   ├─ Context relevance (volatility, trend, session)
   ├─ Recency bonus (not queried in 6+ hours)
   └─ Exploration bonus (20% chance)

3. SELECT DATA SOURCES
   ├─ High Volatility: 6 sources
   ├─ Medium Volatility: 4 sources
   └─ Low Volatility: 3 sources

4. QUERY & ANALYZE
   ├─ Parallel execution (all sources at once)
   ├─ Error handling (graceful degradation)
   └─ Performance tracking

5. GENERATE SIGNALS
   ├─ Whale activity alerts
   ├─ Sentiment shifts
   ├─ Technical breakouts
   ├─ Extreme fear/greed
   └─ Arbitrage opportunities

6. UPDATE LEARNING METRICS
   ├─ Exponential moving average (α = 0.1)
   ├─ Update success rates
   ├─ Update context scores
   └─ Track signal quality
```

---

## 🎓 Adaptive Learning

### Learning Algorithm

**Exponential Moving Average (EMA)** with learning rate α = 0.1:

```
new_metric = (1 - α) × old_metric + α × observation
new_metric = 0.9 × old_metric + 0.1 × observation
```

This means:
- **90% weight** to historical performance
- **10% weight** to new observation
- Smooth adaptation over time

### Metrics Tracked

For each data source:

| Metric | Description | Updated When |
|--------|-------------|--------------|
| **Success Rate** | % of successful API calls | Every query |
| **Signal Quality** | % that generate actionable signals | Every cycle |
| **Context Scores** | Performance in specific conditions | Every cycle |
| **Latency** | Average response time | Every query |
| **Last Called** | Time since last query | Every query |

### Context-Specific Learning

The agent learns which sources work best in different conditions:

- **High Volatility Score**: Performance during volatile markets (>5% moves)
- **Low Volatility Score**: Performance during stable markets (<2% moves)
- **Bullish Score**: Effectiveness in uptrends
- **Bearish Score**: Effectiveness in downtrends
- **Session Scores**: Optimal trading times (Asian/European/American)

### Exploration vs Exploitation

**Exploration Rate**: 20%
- 80% of time: Use best-performing sources (exploitation)
- 20% of time: Try underused sources (exploration)

**Recency Bonus**: Sources not queried in 6+ hours get priority
- Ensures diversity
- Prevents over-reliance on single sources
- Discovers hidden opportunities

---

## 🚨 Signal Generation

### Signal Types

| Signal Type | Trigger | Severity | Target Agents |
|-------------|---------|----------|---------------|
| **WHALE_ACTIVITY** | >100 BTC transactions | HIGH | bitcoin-orchestrator, risk-manager |
| **POSITIVE_NARRATIVE** | Bullish sentiment | MEDIUM | bitcoin-orchestrator |
| **NEGATIVE_NARRATIVE** | Bearish sentiment | MEDIUM | bitcoin-orchestrator |
| **TECHNICAL_BREAKOUT** | STRONG_BUY/SELL | HIGH | bitcoin-orchestrator, trading-executor |
| **EXTREME_GREED** | Fear & Greed >75 | MEDIUM | risk-manager |
| **EXTREME_FEAR** | Fear & Greed <25 | MEDIUM | bitcoin-orchestrator |
| **ARBITRAGE_OPPORTUNITY** | Price spread >0.5% | LOW | trading-executor |

### Signal Structure

```python
@dataclass
class MarketSignal:
    signal_type: str              # Type of signal
    severity: SignalSeverity      # CRITICAL/HIGH/MEDIUM/LOW
    confidence: float             # 0-1 confidence score
    message: str                  # Human-readable description
    data: Dict[str, Any]          # Raw data
    timestamp: datetime           # When generated
    source: str                   # Which data source
    recommended_action: str       # Suggested action
    target_agents: List[str]      # Which agents to notify
```

---

## 📈 Performance Tracking

### Cycle Metrics

Each cycle logs:
- Duration (execution time)
- Market context (price, volatility, trend)
- Sources selected
- Source scores
- Successful queries
- Signals generated
- Signal details

### Agent Statistics

```python
report = agent.get_performance_report()

{
    "cycles_completed": 10,
    "total_signals_generated": 23,
    "avg_cycle_duration": "2.45s",
    "source_performance": {
        "whaleMovements": {
            "success_rate": "95.00%",
            "signal_quality": "60.00%",
            "total_calls": 20,
            "quality_signals": 12
        },
        ...
    },
    "signal_distribution": {
        "WHALE_ACTIVITY": 5,
        "TECHNICAL_BREAKOUT": 8,
        "EXTREME_FEAR": 2,
        ...
    }
}
```

---

## 🔧 Configuration

### Learning Parameters

```python
# Core learning settings
LEARNING_RATE = 0.1           # 10% weight to new observations
EXPLORATION_RATE = 0.2        # 20% chance to explore
RECENCY_BONUS_HOURS = 6       # Bonus after 6 hours

# Source selection
HIGH_VOLATILITY_SOURCES = 6   # Query 6 sources when volatile
MEDIUM_VOLATILITY_SOURCES = 4 # Query 4 sources normally
LOW_VOLATILITY_SOURCES = 3    # Query 3 sources when stable

# Signal thresholds
WHALE_THRESHOLD_BTC = 100     # 100 BTC = whale transaction
FUNDING_RATE_THRESHOLD = 0.05 # 5% funding rate
FEAR_GREED_EXTREME_HIGH = 75  # Extreme greed
FEAR_GREED_EXTREME_LOW = 25   # Extreme fear
RSI_OVERBOUGHT = 70           # RSI overbought
RSI_OVERSOLD = 30             # RSI oversold
```

---

## 🚀 Usage

### Basic Usage

```python
from data_interfaces.market_hunter_agent import MarketHunterAgent

# Initialize agent
agent = MarketHunterAgent()

# Run one cycle
result = await agent.run_cycle()
print(f"Generated {result['signals_generated']} signals")

# Get performance report
report = agent.get_performance_report()
print(f"Success rate: {report['source_performance']}")
```

### Continuous Monitoring

```python
import asyncio

async def continuous_monitoring():
    agent = MarketHunterAgent()
    
    while True:
        # Run cycle
        result = await agent.run_cycle()
        
        # Process signals
        for signal in result.get('signals', []):
            if signal['severity'] in ['critical', 'high']:
                # Alert other agents
                notify_agents(signal)
        
        # Wait 5 minutes
        await asyncio.sleep(300)

asyncio.run(continuous_monitoring())
```

---

## 📊 Integration with Other Agents

The Market Hunter Agent is designed to work with:

### 1. Bitcoin Orchestrator Agent
- **Receives**: All market signals
- **Uses**: To make trading decisions
- **Signals**: POSITIVE_NARRATIVE, NEGATIVE_NARRATIVE, TECHNICAL_BREAKOUT, EXTREME_FEAR

### 2. Risk Manager Agent
- **Receives**: Risk-related signals
- **Uses**: To adjust position sizes
- **Signals**: WHALE_ACTIVITY, EXTREME_GREED

### 3. Trading Executor Agent
- **Receives**: Execution signals
- **Uses**: To execute trades
- **Signals**: TECHNICAL_BREAKOUT, ARBITRAGE_OPPORTUNITY

### Signal Flow

```
Market Hunter Agent
       │
       ├─ WHALE_ACTIVITY ──────────┬─> Bitcoin Orchestrator
       │                           └─> Risk Manager
       │
       ├─ POSITIVE_NARRATIVE ──────> Bitcoin Orchestrator
       │
       ├─ TECHNICAL_BREAKOUT ──────┬─> Bitcoin Orchestrator
       │                           └─> Trading Executor
       │
       ├─ EXTREME_GREED ───────────> Risk Manager
       │
       └─ ARBITRAGE_OPPORTUNITY ───> Trading Executor
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_market_hunter.py
```

### Tests Include:

1. ✅ Agent initialization (7 sources)
2. ✅ Market context assessment
3. ✅ Source scoring & selection
4. ✅ Data source querying
5. ✅ Signal generation
6. ✅ Learning metrics update
7. ✅ Full cycle execution
8. ✅ Performance reporting
9. ✅ Multiple cycles (learning evolution)

---

## 📈 Expected Performance

### Initial Performance (Cycle 1)
- All sources start at 50% success rate
- All sources start at 50% signal quality
- Random exploration high (20%)

### After 10 Cycles
- Sources adjust to actual performance (60-95%)
- Context scores optimize (best sources for each condition)
- Intelligent selection based on learning

### After 100 Cycles
- Fully optimized source selection
- High-quality signal generation (>80% actionable)
- Minimal wasted API calls

---

## 🔮 Future Enhancements

As mentioned in the original Market Hunter docs:

### 1. Meta-Learning
Learn the optimal learning rate itself:
- Some sources need faster adaptation (news)
- Others need slower (technical indicators)

### 2. Multi-Objective Optimization
Balance multiple goals:
- Signal accuracy (primary)
- API cost (secondary)
- Latency (tertiary)

### 3. Causal Inference
Track signal impact:
- Did whale alert predict price move?
- How long is the lag?
- Which signals lead, which lag?

### 4. Collaborative Filtering
Learn from other agents:
- Share learnings across agent instances
- Distributed knowledge base
- Faster convergence

### 5. Anomaly Detection
Identify unusual patterns:
- Unprecedented whale activity
- Sudden sentiment shifts
- Black swan events

### 6. Natural Language Explanations
Generate human-readable explanations:
- "Selected whaleMovements because last 3 whale alerts predicted rallies"
- "Skipping narrativeShifts due to low performance in current volatility"

---

## 🎯 Key Advantages

### 1. **Adaptive Learning**
- ✅ Improves over time automatically
- ✅ No manual tuning required
- ✅ Adapts to changing market dynamics

### 2. **Context-Aware**
- ✅ Adjusts to volatility levels
- ✅ Responds to market trends
- ✅ Optimizes for trading sessions

### 3. **Exploration vs Exploitation**
- ✅ Balances proven sources with discovery
- ✅ Prevents over-reliance on single sources
- ✅ Continuously searches for opportunities

### 4. **Goal-Oriented**
- ✅ Clear objectives (signal generation)
- ✅ Measurable KPIs (signal quality)
- ✅ Cost optimization

### 5. **Fully Integrated**
- ✅ Leverages all 7 data sources
- ✅ Uses Sentiment Analyzer module
- ✅ Uses Technical Indicators module
- ✅ Generates actionable signals

---

## 📚 References

- Original Market Hunter documentation: `docs/markethunteragent.md`
- Data sources: 7 implemented interfaces
- Advanced modules: Sentiment Analyzer, Technical Indicators
- Test suite: `test_market_hunter.py`

---

## 🎉 Conclusion

The Market Hunter Agent successfully integrates all our perfected data sources into an intelligent, adaptive, goal-oriented system that:

1. **Learns** from every cycle
2. **Adapts** to market conditions
3. **Generates** actionable signals
4. **Optimizes** for cost and quality
5. **Improves** over time automatically

**Architecture**: ✅ Hybrid (Adaptive Learning + Goal-Oriented)  
**Data Sources**: ✅ 7/8 integrated (87.5%)  
**Advanced Modules**: ✅ Sentiment + Technical  
**Status**: ✅ Fully operational

Ready for deployment! 🚀
