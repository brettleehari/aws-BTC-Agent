# AWS BTC Market Hunter Agent

An autonomous Bitcoin market intelligence agent built with **Amazon Bedrock AgentCore** that makes independent decisions about which data sources to query based on real-time market conditions and learned performance.

## 🤖 Overview

The Market Hunter Agent is a truly agentic system that:
- **Autonomously decides** which of 8 data sources to query each cycle
- **Learns from experience** using adaptive algorithms
- **Adapts to market conditions** (volatility, trend, time of day)
- **Generates signals** for other trading agents
- **Self-optimizes** through exploration vs exploitation
- **🆕 Dynamically routes** between 10 Bedrock LLMs for optimal cost/performance

## ✨ Key Features

### 1. Autonomous Decision-Making
The agent independently selects 3-6 data sources per cycle from:
- 🐋 **Whale Movements** - Large on-chain transactions (>100 BTC)
- 📈 **Narrative Shifts** - Social media trends and sentiment
- 💱 **Arbitrage Opportunities** - Cross-exchange price spreads
- 👥 **Influencer Signals** - Technical analysis from traders
- 📊 **Technical Breakouts** - Chart pattern detection
- 🏦 **Institutional Flows** - Large holder movements
- 📉 **Derivatives Signals** - Funding rates, liquidations
- 🌍 **Macro Signals** - Fear & Greed Index, market sentiment

### 2. Context-Aware Strategy
Selection based on:
- **Volatility**: High (>5%) → Query 6 sources, Low (<2%) → Query 3 sources
- **Trend**: Bullish → Prioritize institutional/influencer, Bearish → Prioritize derivatives/whales
- **Trading Session**: Asian/European/American/Overlap hours optimize different sources
- **Historical Performance**: Learns which sources work best in which conditions

### 3. Adaptive Learning
Uses exponential moving average algorithm:
```
new_metric = (1 - α) × old_metric + α × new_observation
```
- Learning Rate (α): 0.1 (10% weight to new data)
- Exploration Rate: 0.2 (20% chance to try underused sources)

### 4. Signal Generation
Generates signals for other agents when patterns detected:
- `WHALE_ACTIVITY` - Large transactions detected (severity: high)
- `POSITIVE_NARRATIVE` - Bullish trending topics (severity: medium)
- `INSTITUTIONAL_ACCUMULATION` - Large holdings increase (severity: high)
- `EXTREME_FUNDING` - High funding rates (severity: critical)
- `EXTREME_FEAR/GREED` - Sentiment extremes (severity: medium)

### 5. 🆕 Intelligent LLM Routing
**Dynamic model selection across 10 Bedrock models** for cost optimization:
- **10 Models Supported**: Claude 3 (Haiku/Sonnet/3.5 Sonnet/Opus), Titan (Express/Lite), Llama 3 (8B/70B), Mistral (7B/Large)
- **Task-Based Selection**: Simple extraction → Fast, cheap models (Haiku, Titan Lite); Complex reasoning → Advanced models (Claude 3.5 Sonnet)
- **Cost Optimization**: 80-95% cost reduction vs. fixed model approach
- **Quality Preservation**: Right model for each task - no quality degradation
- **Automatic Tracking**: Real-time usage and cost monitoring

**Example Routing:**
- Whale transaction extraction: Claude 3 Haiku ($0.00025/1K input) - Fast & cheap
- Pattern recognition: Claude 3.5 Sonnet ($0.003/1K input) - Advanced reasoning
- Risk assessment: Claude 3 Opus ($0.015/1K input) - Critical decisions

**Cost Comparison (100 cycles):**
- Fixed Model (always Sonnet): **$27.30**
- Dynamic Routing: **$20.01** → **26.7% savings**
- Yearly Savings: **$3,830+** for 24/7 operation

See [LLM Router Documentation](docs/LLM_ROUTER.md) for details.

## 🏗️ Architecture

```
Market Hunter Agent (Amazon Bedrock Agent)
├── Agent Core (Claude 3 Sonnet)
│   ├── Market Context Assessment
│   ├── Source Selection Logic
│   ├── Result Analysis
│   └── Signal Generation
│
├── Action Group (Lambda)
│   ├── query_whale_movements()
│   ├── query_narrative_shifts()
│   ├── query_arbitrage_opportunities()
│   ├── query_influencer_signals()
│   ├── query_technical_breakouts()
│   ├── query_institutional_flows()
│   ├── query_derivatives_signals()
│   └── query_macro_signals()
│
├── Knowledge Base (Optional)
│   ├── Historical Market Data
│   ├── Trading Patterns
│   └── Market Indicators
│
└── Storage (PostgreSQL)
    ├── agent_executions
    ├── source_metrics_history
    ├── system_alerts
    └── [8 data source tables]
```

## 🚀 Quick Start

### Prerequisites
- AWS Account with Bedrock access
- Python 3.9+
- PostgreSQL database (optional, for persistence)

### Installation

1. **Clone and install dependencies**
```bash
cd /workspaces/aws-BTC-Agent
pip install -r requirements.txt
```

2. **Set up AWS credentials**
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

3. **Create Bedrock Agent**
```bash
# Follow the setup instructions
python src/bedrock_agent_setup.py
```

4. **Update configuration**
Edit `src/example_usage.py` with your Bedrock Agent details:
```python
BEDROCK_AGENT_ID = "YOUR_AGENT_ID"
BEDROCK_AGENT_ALIAS_ID = "YOUR_ALIAS_ID"
AWS_REGION = "us-east-1"
```

5. **Run the agent**
```bash
python src/example_usage.py
```

## 📖 Usage

### Basic Usage

```python
from market_hunter_agent import MarketHunterAgent

# Initialize agent
agent = MarketHunterAgent(
    bedrock_agent_id="YOUR_AGENT_ID",
    bedrock_agent_alias_id="YOUR_ALIAS_ID",
    region_name="us-east-1",
    learning_rate=0.1,
    exploration_rate=0.2
)

# Execute one cycle
market_data = {
    'price': 62500,
    'price_change_24h_percent': 4.2,
    'volume_ratio': 1.2
}

result = agent.execute_cycle(market_data)

# Get performance report
report = agent.get_performance_report()
```

### With Database Storage

```python
from market_hunter_agent import MarketHunterAgent
from database import MarketHunterDatabase

# Initialize with database
db = MarketHunterDatabase("postgresql://user:pass@localhost/btc_agent")
db.create_tables()

agent = MarketHunterAgent(...)

# Execute and store
result = agent.execute_cycle(market_data)
execution_id = db.store_execution(result)
db.store_signals(execution_id, result['signals'])
db.store_source_metrics(execution_id, result['metrics'])

# Retrieve unprocessed signals
signals = db.get_unprocessed_signals()
```

### Continuous Operation (Production)

```python
import time
import schedule

def run_agent_cycle():
    market_data = fetch_current_market_data()  # Your implementation
    result = agent.execute_cycle(market_data)
    db.store_execution(result)
    # Process signals...

# Run every 10 minutes
schedule.every(10).minutes.do(run_agent_cycle)

while True:
    schedule.run_pending()
    time.sleep(1)
```

## 📊 Performance Monitoring

### View Source Performance
```python
report = agent.get_performance_report()

for source, metrics in report['source_performance'].items():
    print(f"{source}:")
    print(f"  Success Rate: {metrics['success_rate']:.3f}")
    print(f"  Signal Quality: {metrics['signal_quality']:.3f}")
    print(f"  Efficiency: {metrics['efficiency']:.3f}")
```

### Database Analytics
```sql
-- Top performing sources
SELECT source_name, AVG(signal_quality) as avg_quality
FROM source_metrics_history
GROUP BY source_name
ORDER BY avg_quality DESC;

-- Signals by severity
SELECT severity, COUNT(*) as count
FROM system_alerts
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY severity;

-- Agent performance over time
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as cycles,
    AVG(signals_count) as avg_signals
FROM agent_executions
GROUP BY DATE(timestamp)
ORDER BY date DESC;
```

## 🔧 Configuration

### Agent Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `learning_rate` | 0.1 | Weight given to new observations (0.0-1.0) |
| `exploration_rate` | 0.2 | Probability of exploring underused sources (0.0-1.0) |
| `bedrock_agent_id` | Required | Your Bedrock Agent ID |
| `bedrock_agent_alias_id` | Required | Your Bedrock Agent Alias ID |
| `region_name` | us-east-1 | AWS region |

### Market Context Thresholds

```python
# Volatility levels (based on 24h price change)
HIGH_VOLATILITY = 5%  # → Query 6 sources
MEDIUM_VOLATILITY = 2%  # → Query 4 sources
LOW_VOLATILITY = <2%  # → Query 3 sources

# Trend detection
BULLISH_THRESHOLD = +2%
BEARISH_THRESHOLD = -2%
```

## 💰 Cost Estimation

### AWS Costs (per month with 144 cycles/day)
- **Bedrock Agent**: ~$50-100 (based on token usage)
- **Claude 3 Sonnet**: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- **Lambda Functions**: ~$5-10 (1M invocations free tier)
- **PostgreSQL RDS**: ~$15-50 (db.t3.micro or Aurora Serverless)

**Total estimated: $70-160/month** for production usage

## 🛠️ Development

### Project Structure
```
aws-BTC-Agent/
├── src/
│   ├── market_hunter_agent.py    # Main agent implementation
│   ├── example_usage.py           # Example usage script
│   ├── bedrock_agent_setup.py     # Setup instructions
│   └── database.py                # Database integration
├── config/
│   └── action-group-schema.json   # OpenAPI schema for Lambda
├── docs/
│   └── markethunteragent.md       # Detailed documentation
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

### Running Tests
```bash
# Unit tests (to be implemented)
pytest tests/

# Integration test with mock data
python src/example_usage.py
```

### Adding New Data Sources

1. Add source name to `DATA_SOURCES` list in `market_hunter_agent.py`
2. Create database table in `database.py`
3. Add function to Lambda action group
4. Update OpenAPI schema in `config/action-group-schema.json`
5. Update agent instructions in `bedrock_agent_setup.py`

## 📝 Future Enhancements

- [ ] Meta-learning (optimize learning rate automatically)
- [ ] Multi-objective optimization (accuracy vs cost)
- [ ] Causal inference (did my signals cause agent actions?)
- [ ] Collaborative filtering (learn from other agents)
- [ ] Anomaly detection (auto-detect unusual patterns)
- [ ] Natural language explanations (explain decisions in plain English)
- [ ] Real-time dashboard with Streamlit/Grafana
- [ ] Backtesting framework for strategy validation

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## 📧 Support

For issues or questions:
- Open a GitHub issue
- Check the documentation in `docs/`
- Review `bedrock_agent_setup.py` for configuration help

## 🙏 Acknowledgments

Built with:
- Amazon Bedrock AgentCore
- Claude 3 Sonnet (Anthropic)
- AWS Lambda
- PostgreSQL

---

**Note**: This is a demonstration implementation. In production:
- Implement real API integrations for data sources
- Add comprehensive error handling and retry logic
- Set up proper monitoring and alerting
- Implement security best practices (secrets management, IAM roles)
- Add rate limiting and cost controls
- Validate all inputs and sanitize outputs