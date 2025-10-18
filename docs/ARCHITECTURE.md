# Market Hunter Agent - Architecture Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MARKET HUNTER AGENT SYSTEM                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: MARKET CONTEXT ASSESSMENT                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Market Data Input                     Context Assessment                    │
│  ┌──────────────────┐                 ┌────────────────────┐               │
│  │ • BTC Price      │────────────────▶│ • Volatility Level │               │
│  │ • 24h Change     │                 │   - HIGH (>5%)     │               │
│  │ • Volume Ratio   │                 │   - MEDIUM (2-5%)  │               │
│  │ • Timestamp      │                 │   - LOW (<2%)      │               │
│  └──────────────────┘                 │                    │               │
│                                        │ • Trend Detection  │               │
│                                        │   - BULLISH        │               │
│                                        │   - BEARISH        │               │
│                                        │   - NEUTRAL        │               │
│                                        │                    │               │
│                                        │ • Trading Session  │               │
│                                        │   - ASIAN          │               │
│                                        │   - EUROPEAN       │               │
│                                        │   - AMERICAN       │               │
│                                        │   - OVERLAP        │               │
│                                        └────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: SOURCE SCORING & SELECTION (AUTONOMOUS DECISION)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  8 Data Sources                        Scoring Algorithm                     │
│  ┌─────────────────────────┐          ┌──────────────────────────────┐     │
│  │ 1. whaleMovements       │          │ Score = base_score           │     │
│  │ 2. narrativeShifts      │          │       + context_bonus        │     │
│  │ 3. arbitrageOpps        │─────────▶│       + recency_bonus        │     │
│  │ 4. influencerSignals    │          │       + exploration_bonus    │     │
│  │ 5. technicalBreakouts   │          │                              │     │
│  │ 6. institutionalFlows   │          │ Base Score:                  │     │
│  │ 7. derivativesSignals   │          │  - Success Rate (0-1)        │     │
│  │ 8. macroSignals         │          │  - Signal Quality (0-1)      │     │
│  └─────────────────────────┘          │                              │     │
│                                        │ Context Bonus:               │     │
│                                        │  - Volatility match (+0.4)   │     │
│                                        │  - Trend alignment (+0.2)    │     │
│                                        │  - Session relevance (+0.3)  │     │
│                                        │                              │     │
│                                        │ Recency: +0.05 per cycle     │     │
│                                        │ Exploration: 20% chance      │     │
│                                        └──────────────────────────────┘     │
│                                                     │                        │
│                                                     ▼                        │
│  Source Selection                      ┌──────────────────────────────┐     │
│  ┌─────────────────────────┐          │ HIGH Volatility → 6 sources  │     │
│  │ Selected (3-6 sources)  │◀─────────│ MEDIUM Volatility → 4 sources│     │
│  │ Based on top scores     │          │ LOW Volatility → 3 sources   │     │
│  └─────────────────────────┘          └──────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: AMAZON BEDROCK AGENT INVOCATION                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  AMAZON BEDROCK AGENT                                           │        │
│  │  ┌────────────────────────────────────────────────────────┐    │        │
│  │  │  Foundation Model: Claude 3 Sonnet                     │    │        │
│  │  │  ┌──────────────────────────────────────────────────┐ │    │        │
│  │  │  │  Agent Instructions:                             │ │    │        │
│  │  │  │  • Analyze market data from selected sources     │ │    │        │
│  │  │  │  • Extract actionable insights                   │ │    │        │
│  │  │  │  • Identify trading signals and patterns         │ │    │        │
│  │  │  │  • Provide confidence scores                     │ │    │        │
│  │  │  └──────────────────────────────────────────────────┘ │    │        │
│  │  └────────────────────────────────────────────────────────┘    │        │
│  │                              │                                  │        │
│  │  ┌───────────────────────────▼──────────────────────────┐      │        │
│  │  │  Action Group: MarketDataQueries                     │      │        │
│  │  │  ┌──────────────────────────────────────────────┐   │      │        │
│  │  │  │  AWS Lambda Function                         │   │      │        │
│  │  │  │                                              │   │      │        │
│  │  │  │  def lambda_handler(event, context):        │   │      │        │
│  │  │  │      function = event['function']           │   │      │        │
│  │  │  │                                              │   │      │        │
│  │  │  │      if function == 'query_whale_movements':│   │      │        │
│  │  │  │          return fetch_whale_data()          │   │      │        │
│  │  │  │      elif function == 'query_derivatives':  │   │      │        │
│  │  │  │          return fetch_derivatives_data()    │   │      │        │
│  │  │  │      # ... other 6 data sources             │   │      │        │
│  │  │  └──────────────────────────────────────────────┘   │      │        │
│  │  └───────────────────────────────────────────────────────┘      │        │
│  │                              │                                  │        │
│  │  ┌───────────────────────────▼──────────────────────────┐      │        │
│  │  │  Knowledge Base (Optional)                           │      │        │
│  │  │  • Historical market data                            │      │        │
│  │  │  • Trading patterns                                  │      │        │
│  │  │  • Indicator references                              │      │        │
│  │  └──────────────────────────────────────────────────────┘      │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                   │                                          │
│                                   ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  Query Results                                                  │        │
│  │  ┌───────────────────────────────────────────────────────┐     │        │
│  │  │ source: "whaleMovements"                              │     │        │
│  │  │ data: "Detected 3 large transactions >100 BTC..."    │     │        │
│  │  │ timestamp: "2025-10-18T12:00:00Z"                    │     │        │
│  │  │ success: true                                         │     │        │
│  │  └───────────────────────────────────────────────────────┘     │        │
│  └─────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: RESULT ANALYSIS & SIGNAL GENERATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Analysis Pipeline                     Signal Generation                     │
│  ┌────────────────────────┐           ┌─────────────────────────────┐       │
│  │ Combine all results    │──────────▶│ Pattern Detection:          │       │
│  │ from selected sources  │           │                             │       │
│  └────────────────────────┘           │ IF whale_tx > 100 BTC       │       │
│             │                          │ THEN WHALE_ACTIVITY         │       │
│             ▼                          │ severity: HIGH              │       │
│  ┌────────────────────────┐           │                             │       │
│  │ Send to Bedrock Agent  │           │ IF funding_rate > 5%        │       │
│  │ for pattern analysis   │           │ THEN EXTREME_FUNDING        │       │
│  └────────────────────────┘           │ severity: CRITICAL          │       │
│             │                          │                             │       │
│             ▼                          │ IF fear_greed < 25          │       │
│  ┌────────────────────────┐           │ THEN EXTREME_FEAR           │       │
│  │ Identify signals:      │           │ severity: MEDIUM            │       │
│  │ • Whale activity       │           │                             │       │
│  │ • Sentiment extremes   │           │ ... (9 signal types)        │       │
│  │ • Funding anomalies    │           └─────────────────────────────┘       │
│  │ • Narrative shifts     │                        │                        │
│  └────────────────────────┘                        ▼                        │
│                                        ┌─────────────────────────────┐       │
│                                        │ Generated Signals:          │       │
│                                        │ ┌─────────────────────────┐ │       │
│                                        │ │ signal_type             │ │       │
│                                        │ │ severity                │ │       │
│                                        │ │ confidence              │ │       │
│                                        │ │ message                 │ │       │
│                                        │ │ recommended_action      │ │       │
│                                        │ │ target_agents[]         │ │       │
│                                        │ └─────────────────────────┘ │       │
│                                        └─────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: ADAPTIVE LEARNING                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Update Metrics                        Learning Algorithm                    │
│  ┌─────────────────────────┐          ┌──────────────────────────────┐      │
│  │ For each source used:   │          │ Exponential Moving Average:  │      │
│  │                         │          │                              │      │
│  │ • Success? (Y/N)        │─────────▶│ new = (1-α) × old + α × obs  │      │
│  │ • Quality? (Y/N)        │          │                              │      │
│  │ • Contributed signal?   │          │ α = 0.1 (learning rate)      │      │
│  │                         │          │                              │      │
│  │ Update:                 │          │ For each metric:             │      │
│  │ • success_rate          │          │ • success_rate               │      │
│  │ • signal_quality        │          │ • signal_quality             │      │
│  │ • total_calls           │          │ • last_used_cycles_ago       │      │
│  └─────────────────────────┘          └──────────────────────────────┘      │
│                                                                               │
│  Exploration vs Exploitation           Performance Tracking                  │
│  ┌─────────────────────────┐          ┌──────────────────────────────┐      │
│  │ 80% - Use best sources  │          │ Store in database:           │      │
│  │        (exploitation)   │          │ • Execution logs             │      │
│  │                         │          │ • Source metrics history     │      │
│  │ 20% - Try new sources   │          │ • Generated signals          │      │
│  │        (exploration)    │          │ • Market context             │      │
│  └─────────────────────────┘          └──────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6: SIGNAL DISTRIBUTION & STORAGE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  PostgreSQL Database                   Signal Distribution                   │
│  ┌─────────────────────────┐          ┌──────────────────────────────┐      │
│  │ Tables:                 │          │ Target Agents:               │      │
│  │                         │          │                              │      │
│  │ • agent_executions      │          │ • bitcoin-orchestrator       │      │
│  │ • whale_movements       │          │ • risk-manager               │      │
│  │ • narrative_shifts      │──────────▶│ • trading-agent             │      │
│  │ • arbitrage_opps        │          │ • portfolio-optimizer        │      │
│  │ • influencer_signals    │          │                              │      │
│  │ • technical_breakouts   │          │ Via:                         │      │
│  │ • institutional_flows   │          │ • AWS EventBridge            │      │
│  │ • derivatives_signals   │          │ • SQS Queues                 │      │
│  │ • macro_signals         │          │ • SNS Topics                 │      │
│  │ • system_alerts         │          │ • Direct Invocation          │      │
│  │ • source_metrics_history│          └──────────────────────────────┘      │
│  └─────────────────────────┘                                                 │
│                                                                               │
│  Analytics & Reporting                                                       │
│  ┌─────────────────────────────────────────────────────────────┐            │
│  │ • Source performance ranking                                │            │
│  │ • Signal effectiveness tracking                             │            │
│  │ • Learning progress visualization                           │            │
│  │ • Cost optimization metrics                                 │            │
│  │ • Market condition correlation analysis                     │            │
│  └─────────────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTINUOUS OPERATION (Every 10 Minutes)                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │
│  │Cycle │  │Cycle │  │Cycle │  │Cycle │  │Cycle │  │Cycle │  │Cycle │     │
│  │  1   │─▶│  2   │─▶│  3   │─▶│  4   │─▶│  5   │─▶│  6   │─▶│  ...  │     │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘     │
│     │         │         │         │         │         │         │           │
│     ▼         ▼         ▼         ▼         ▼         ▼         ▼           │
│  Learn     Learn     Learn     Learn     Learn     Learn     Learn          │
│  Adapt     Adapt     Adapt     Adapt     Adapt     Adapt     Adapt          │
│  Improve   Improve   Improve   Improve   Improve   Improve   Improve        │
│                                                                               │
│  Agent gets smarter with each cycle! 🧠                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Metrics Dashboard

```
┌────────────────────────────────────────────────────────────────┐
│  MARKET HUNTER AGENT - PERFORMANCE DASHBOARD                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Execution Metrics:                                            │
│  ┌──────────────┬──────────────┬──────────────┬─────────────┐ │
│  │ Total Cycles │   Duration   │   Signals    │  Efficiency │ │
│  │     144      │   12.3s avg  │      47      │    0.847    │ │
│  └──────────────┴──────────────┴──────────────┴─────────────┘ │
│                                                                 │
│  Top Sources (by Signal Quality):                              │
│  ┌──────────────────────────┬─────────┬─────────┬──────────┐  │
│  │        Source            │ Quality │ Success │   Calls  │  │
│  ├──────────────────────────┼─────────┼─────────┼──────────┤  │
│  │  derivativesSignals      │  0.892  │  0.945  │    87    │  │
│  │  whaleMovements          │  0.854  │  0.923  │    95    │  │
│  │  institutionalFlows      │  0.831  │  0.887  │    72    │  │
│  │  influencerSignals       │  0.789  │  0.912  │    68    │  │
│  │  narrativeShifts         │  0.723  │  0.856  │    58    │  │
│  │  technicalBreakouts      │  0.698  │  0.834  │    52    │  │
│  │  macroSignals            │  0.654  │  0.901  │    89    │  │
│  │  arbitrageOpportunities  │  0.612  │  0.778  │    35    │  │
│  └──────────────────────────┴─────────┴─────────┴──────────┘  │
│                                                                 │
│  Signal Distribution (Last 24h):                               │
│  ┌───────────────────────────────┬───────┬────────────────┐   │
│  │         Signal Type           │ Count │    Severity    │   │
│  ├───────────────────────────────┼───────┼────────────────┤   │
│  │  WHALE_ACTIVITY               │   12  │  HIGH          │   │
│  │  EXTREME_FUNDING              │    3  │  CRITICAL      │   │
│  │  INSTITUTIONAL_ACCUMULATION   │    8  │  HIGH          │   │
│  │  POSITIVE_NARRATIVE           │   15  │  MEDIUM        │   │
│  │  EXTREME_GREED                │    4  │  MEDIUM        │   │
│  │  EXTREME_FEAR                 │    2  │  MEDIUM        │   │
│  │  TECHNICAL_BREAKOUT           │    3  │  HIGH          │   │
│  └───────────────────────────────┴───────┴────────────────┘   │
│                                                                 │
│  Learning Progress:  ████████████████░░░░  80% optimized       │
│  Exploration Rate:   ████░░░░░░░░░░░░░░░░  20% active          │
└────────────────────────────────────────────────────────────────┘
```

## Decision Tree Example

```
Market Context: BTC $62,500 (+4.2%), HIGH volatility, BULLISH, American hours

                         ┌─────────────────┐
                         │  Market Hunter  │
                         │      Agent      │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │  Context Assessment        │
                    │  • Volatility: HIGH        │
                    │  • Trend: BULLISH          │
                    │  • Session: AMERICAN       │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Calculate Scores          │
                    │  • derivatives: 0.92       │
                    │  • whales: 0.85            │
                    │  • institutional: 0.83     │
                    │  • influencer: 0.78        │
                    │  • narrative: 0.72         │
                    │  • technical: 0.68         │
                    │  • macro: 0.62             │
                    │  • arbitrage: 0.55         │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Select Top 6 (HIGH vol)   │
                    │  ✓ derivativesSignals      │
                    │  ✓ whaleMovements          │
                    │  ✓ institutionalFlows      │
                    │  ✓ influencerSignals       │
                    │  ✓ narrativeShifts         │
                    │  ✓ technicalBreakouts      │
                    └─────────────┬──────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
    ┌───────▼────────┐   ┌───────▼────────┐   ┌───────▼────────┐
    │ Query Bedrock  │   │ Query Bedrock  │   │ Query Bedrock  │
    │    Agent       │   │    Agent       │   │    Agent       │
    │ (derivatives)  │   │   (whales)     │   │(institutional) │
    └───────┬────────┘   └───────┬────────┘   └───────┬────────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Analyze Results           │
                    │  • 2 whale txs detected    │
                    │  • Extreme funding: 0.06%  │
                    │  • 5 bullish narratives    │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Generate Signals          │
                    │  → WHALE_ACTIVITY          │
                    │  → EXTREME_FUNDING         │
                    │  → POSITIVE_NARRATIVE      │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Update Learning           │
                    │  ✓ derivatives quality↑    │
                    │  ✓ whales success↑         │
                    │  ✗ institutional no data   │
                    └────────────────────────────┘
```

This architecture demonstrates true agentic behavior through autonomous decision-making,
adaptive learning, and context-aware optimization! 🚀
