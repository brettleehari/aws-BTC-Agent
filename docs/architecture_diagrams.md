# Data Interfaces Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Amazon Bedrock Agent                          │
│  (Discovers capabilities via OpenAPI action group schemas)      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ Invokes via Lambda
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Lambda Handler (Future)                      │
│              Parse event → Create request → Execute              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Data Interface Manager                         │
│  • Automatic source selection                                    │
│  • Fallback on failure                                          │
│  • Response caching                                             │
│  • Circuit breaker protection                                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
                ▼           ▼           ▼
        ┌───────────┐ ┌──────────┐ ┌─────────────┐
        │ CoinGecko │ │Glassnode │ │  Sentiment  │
        │  Source   │ │  Source  │ │   Analyzer  │
        └─────┬─────┘ └────┬─────┘ └──────┬──────┘
              │            │              │
              │            │              │
              ▼            ▼              ▼
        ┌──────────────────────────────────────┐
        │      External APIs                    │
        │  • CoinGecko API                     │
        │  • Glassnode API                     │
        │  • Alternative.me Fear & Greed       │
        └──────────────────────────────────────┘
```

## Component Interaction Flow

```
┌──────────────┐
│   Request    │
│ (DataRequest)│
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Capability Registry                │
│ • Find matching sources              │
│ • Calculate quality scores           │
│ • Rank by suitability               │
└──────┬──────────────────────────────┘
       │
       │ Sources ranked by score
       │
       ▼
┌─────────────────────────────────────┐
│   Data Interface Manager             │
│ • Check cache                        │
│ • Check circuit breakers            │
│ • Try primary source                │
└──────┬──────────────────────────────┘
       │
       ├──► Cache Hit? ──► Return cached response
       │
       ├──► Circuit Open? ──► Try next source
       │
       └──► Fetch from source
              │
              ▼
       ┌─────────────────┐
       │ Source Fetch    │
       │ • Validate      │
       │ • Transform     │
       │ • Return        │
       └────────┬────────┘
                │
                ├──► Success ──► Cache response
                │               └──► Return to caller
                │
                └──► Failure ──► Record failure
                                └──► Try fallback
```

## Quality Scoring Algorithm

```
┌─────────────────────────────────────────────────────────┐
│                  Quality Score Calculation               │
│                                                          │
│  Input: DataRequest + SourceMetadata                     │
│                                                          │
│  Step 1: Reliability Score (40%)                        │
│  ├─ Historical uptime                                   │
│  ├─ Error rate                                          │
│  └─ Success rate                                        │
│                                                          │
│  Step 2: Capability Match (30%)                         │
│  ├─ Supports data type?                                 │
│  ├─ Has required capabilities?                          │
│  └─ Feature completeness                                │
│                                                          │
│  Step 3: Speed Score (20%)                              │
│  ├─ Real-time: 1.0                                      │
│  ├─ Fast: 0.8                                           │
│  ├─ Moderate: 0.5                                       │
│  └─ Slow: 0.3                                           │
│                                                          │
│  Step 4: Cost Score (20%)                               │
│  ├─ Free: 1.0                                           │
│  ├─ Freemium: 0.8                                       │
│  ├─ Paid: 0.5                                           │
│  └─ Subscription: 0.4                                   │
│                                                          │
│  Output: Score 0.0 - 1.0                                │
└─────────────────────────────────────────────────────────┘
```

## Circuit Breaker State Machine

```
                  ┌──────────────────┐
                  │   CLOSED         │
                  │  (Operational)   │
                  │                  │
                  │ Requests pass    │
                  │ through          │
                  └────────┬─────────┘
                           │
                           │ 5 consecutive
                           │ failures
                           │
                           ▼
      Success      ┌──────────────────┐
    ◄──────────────┤    OPEN          │
                   │  (Blocked)       │
                   │                  │
                   │ Requests fail    │
                   │ fast             │
                   └────────┬─────────┘
                            │
                            │ After 60 seconds
                            │
                            ▼
                   ┌──────────────────┐
                   │   HALF-OPEN      │
                   │  (Testing)       │
                   │                  │
                   │ Next request     │
                   │ determines       │
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              │                           │
         Success                      Failure
              │                           │
              ▼                           ▼
      Back to CLOSED              Back to OPEN
```

## Data Source Implementations

```
┌────────────────────────────────────────────────────────────────┐
│                        CoinGecko                                │
│  Cost: Free/Freemium                                           │
│  Rate: 50/min, 10k/day                                         │
├────────────────────────────────────────────────────────────────┤
│  Data Types:                                                   │
│  • PRICE - Real-time cryptocurrency prices                     │
│  • MARKET_CAP - Market capitalization                          │
│  • VOLUME - 24h trading volume                                 │
│                                                                │
│  Capabilities:                                                 │
│  • REAL_TIME - Live price updates                              │
│  • HISTORICAL - Historical data                                │
│  • MULTI_CURRENCY - Multiple fiat currencies                   │
│                                                                │
│  Best For: Price queries, market overview, quick checks        │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                        Glassnode                                │
│  Cost: Subscription ($$$)                                      │
│  Rate: 10/min, 10k/day                                         │
├────────────────────────────────────────────────────────────────┤
│  Data Types:                                                   │
│  • ON_CHAIN - Network metrics, addresses                       │
│  • WHALE_TRANSACTIONS - Large holder movements                 │
│  • EXCHANGE_FLOWS - Exchange inflows/outflows                  │
│  • NETWORK_METRICS - Hash rate, difficulty                     │
│                                                                │
│  Capabilities:                                                 │
│  • WHALE_TRACKING - Track large transactions                   │
│  • EXCHANGE_MONITORING - Monitor exchange activity             │
│  • ADVANCED_ANALYTICS - MVRV, SOPR metrics                     │
│                                                                │
│  Best For: On-chain analysis, whale tracking, advanced metrics │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                    Sentiment Analyzer                           │
│  Cost: Free                                                    │
│  Rate: 30/min, unlimited/day                                   │
├────────────────────────────────────────────────────────────────┤
│  Data Types:                                                   │
│  • SOCIAL_SENTIMENT - Fear & Greed Index                       │
│  • NEWS - News sentiment (future)                              │
│                                                                │
│  Capabilities:                                                 │
│  • SENTIMENT_ANALYSIS - Market mood assessment                 │
│  • AGGREGATION - Multiple sentiment sources                    │
│  • TIME_SERIES - Historical sentiment data                     │
│                                                                │
│  Best For: Sentiment analysis, market mood, fear/greed         │
└────────────────────────────────────────────────────────────────┘
```

## Bedrock Action Groups

```
┌─────────────────────────────────────────────────────────────┐
│                    PriceData Action Group                    │
├─────────────────────────────────────────────────────────────┤
│  GET /price          - Get cryptocurrency price             │
│  GET /market_cap     - Get market capitalization            │
│  GET /volume         - Get trading volume                   │
├─────────────────────────────────────────────────────────────┤
│  Sources: CoinGecko                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   OnChainData Action Group                   │
├─────────────────────────────────────────────────────────────┤
│  GET /on_chain           - Get on-chain metrics             │
│  GET /whale_transactions - Get whale movements              │
│  GET /exchange_flows     - Get exchange flows               │
├─────────────────────────────────────────────────────────────┤
│  Sources: Glassnode                                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 SentimentData Action Group                   │
├─────────────────────────────────────────────────────────────┤
│  GET /social_sentiment   - Get sentiment analysis           │
│  GET /news              - Get news sentiment                │
├─────────────────────────────────────────────────────────────┤
│  Sources: SentimentAnalyzer                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  NetworkData Action Group                    │
├─────────────────────────────────────────────────────────────┤
│  GET /network_metrics    - Get network health               │
├─────────────────────────────────────────────────────────────┤
│  Sources: Glassnode                                         │
└─────────────────────────────────────────────────────────────┘
```

## Caching Architecture

```
┌───────────────────────────────────────────────────────┐
│                  Request arrives                       │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ Cache enabled?│
              └───────┬───────┘
                      │
           ┌──────────┼──────────┐
          Yes                    No
           │                      │
           ▼                      ▼
    ┌─────────────┐       ┌──────────────┐
    │ Generate    │       │ Fetch from   │
    │ cache key   │       │ source       │
    └──────┬──────┘       └──────────────┘
           │
           ▼
    ┌─────────────┐
    │ Cache hit?  │
    └──────┬──────┘
           │
    ┌──────┼──────┐
   Yes            No
    │              │
    ▼              ▼
┌────────┐  ┌──────────────┐
│ Return │  │ Fetch from   │
│ cached │  │ source       │
│ data   │  └──────┬───────┘
└────────┘         │
                   ▼
            ┌──────────────┐
            │ Cache result │
            │ (TTL: 60s)   │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ Return to    │
            │ caller       │
            └──────────────┘
```

## Manager Decision Tree

```
Fetch Request
    │
    ▼
┌───────────────────┐
│ Check cache       │
└────────┬──────────┘
         │
    Hit? │ No
         │
         ▼
┌───────────────────┐
│ Get source        │
│ rankings          │
└────────┬──────────┘
         │
         ▼
┌───────────────────┐
│ For each source:  │
│                   │
│ 1. Circuit open?  │──Yes──┐
│                   │       │
│ 2. Health good?   │──No───┤
│                   │       │
│ 3. Try fetch      │       │
│                   │       │
│ 4. Success?       │──Yes──► Return
│                   │       │
└────────┬──────────┘       │
         │                  │
         No                 │
         │                  │
    Fallback               │
    enabled?               │
         │                  │
    ┌────┼────┐            │
   Yes       No             │
    │         │             │
    │         └─────────────┘
    │
    ▼
Try next
source
```

---

*Architecture diagrams for AWS BTC Market Hunter Agent Data Interfaces Module*
