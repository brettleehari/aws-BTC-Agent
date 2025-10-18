# 🚀 Market Hunter Agent - Quick Start Guide

## What You Have Now

A complete **autonomous Bitcoin market intelligence agent** built with Amazon Bedrock AgentCore!

## 📁 Project Structure

```
aws-BTC-Agent/
├── 📄 README.md                          ← Start here! Complete documentation
├── 📋 IMPLEMENTATION_SUMMARY.md          ← What was built & how it works
├── 🔧 requirements.txt                   ← Python dependencies
├── 🚀 deploy.sh                          ← Automated deployment script
│
├── src/                                  ← Core implementation
│   ├── market_hunter_agent.py           ← Main agent (600+ lines) ⭐
│   ├── example_usage.py                 ← Demo script
│   ├── production_service.py            ← Production wrapper
│   ├── bedrock_agent_setup.py           ← AWS setup guide
│   └── database.py                      ← PostgreSQL integration
│
├── config/
│   └── action-group-schema.json         ← OpenAPI schema for Lambda
│
└── docs/
    ├── markethunteragent.md             ← Original requirements
    ├── ARCHITECTURE.md                  ← ASCII architecture diagrams
    └── MERMAID_DIAGRAMS.md              ← Interactive Mermaid diagrams ⭐
```

## 🎯 Core Concepts

### What Makes This "Agentic"?

❌ **Traditional Approach:** Always query all 8 data sources
```python
for source in all_sources:
    query(source)  # Wasteful, not context-aware
```

✅ **Agentic Approach:** Agent decides which sources to query
```python
context = assess_market()  # Volatility, trend, session
scores = calculate_relevance(context, history)
selected = select_best(scores, exploration_rate)  # Smart selection!
learn_from_results(selected)  # Gets smarter over time
```

### Key Features

1. **🧠 Autonomous Decision-Making**
   - Selects 3-6 of 8 data sources per cycle
   - Decisions based on market context + learned performance

2. **📊 Context-Aware**
   - HIGH volatility (>5%) → Query 6 sources
   - MEDIUM volatility (2-5%) → Query 4 sources
   - LOW volatility (<2%) → Query 3 sources

3. **🎓 Adaptive Learning**
   - Learns which sources work best in which conditions
   - Uses exponential moving average: `new = 0.9×old + 0.1×observation`

4. **🔍 Pattern Detection**
   - Generates signals: WHALE_ACTIVITY, EXTREME_FUNDING, etc.
   - Sends to other agents (orchestrator, risk-manager, trading-agent)

5. **🔄 Self-Optimizing**
   - Exploration (20%): Try underused sources
   - Exploitation (80%): Use proven sources

## 🏃 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
cd /workspaces/aws-BTC-Agent
pip install -r requirements.txt
```

### 2. Configure AWS
```bash
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1)
```

### 3. View Setup Instructions
```bash
python src/bedrock_agent_setup.py
```

### 4. Test Locally (Without Bedrock)
```bash
# Run demo with simulated data
python src/example_usage.py
```

## 📊 View the Diagrams

### Option 1: Open in VS Code with Mermaid Extension
```bash
# Install extension
code --install-extension bierner.markdown-mermaid

# Open diagrams
code docs/MERMAID_DIAGRAMS.md
```

### Option 2: View on GitHub
Push to GitHub and view `docs/MERMAID_DIAGRAMS.md` - diagrams render automatically!

### Option 3: Online Viewer
Copy diagram code from `MERMAID_DIAGRAMS.md` to: https://mermaid.live/

## 🎨 Diagram Overview

We created **7 comprehensive diagrams**:

1. **System Architecture** - Complete system overview
2. **Sequence Diagram** - Step-by-step execution flow
3. **Learning Algorithm** - How agent improves over time
4. **State Machine** - Agent states and transitions
5. **Component Interaction** - AWS services integration
6. **Data Flow** - End-to-end data journey
7. **Database Schema** - Data storage structure

## 🚀 Deployment Steps

### Phase 1: Create AWS Bedrock Agent (30 min)

1. **Create IAM Role**
   ```bash
   # See bedrock_agent_setup.py for trust policy
   ```

2. **Create Lambda Functions** (8 functions)
   ```bash
   # One for each data source
   # Template in bedrock_agent_setup.py
   ```

3. **Create Bedrock Agent**
   ```bash
   aws bedrock-agent create-agent \
     --agent-name MarketHunterAgent \
     --foundation-model anthropic.claude-3-sonnet-20240229-v1:0
   ```

4. **Create Agent Alias**
   ```bash
   aws bedrock-agent create-agent-alias \
     --agent-id YOUR_AGENT_ID \
     --agent-alias-name prod
   ```

### Phase 2: Set Up Database (15 min)

```bash
# Create PostgreSQL RDS instance
aws rds create-db-instance \
  --db-instance-identifier market-hunter-db \
  --db-instance-class db.t3.micro \
  --engine postgres

# Initialize tables
python -c "from src.database import MarketHunterDatabase; \
  db = MarketHunterDatabase('postgresql://...'); \
  db.create_tables()"
```

### Phase 3: Deploy Application (15 min)

```bash
# Update .env with your agent details
cat > .env << EOF
BEDROCK_AGENT_ID=your-agent-id
BEDROCK_AGENT_ALIAS_ID=your-alias-id
DATABASE_URL=postgresql://user:pass@host/db
AWS_REGION=us-east-1
EOF

# Test it
python src/example_usage.py

# Run in production
python src/production_service.py
```

## 📈 Monitoring

### View Logs
```bash
# CloudWatch logs
aws logs tail /aws/lambda/market-hunter-actions --follow

# Application logs
tail -f /var/log/market-hunter.log
```

### Query Performance
```sql
-- Top performing sources
SELECT source_name, AVG(signal_quality) as quality
FROM source_metrics_history
GROUP BY source_name
ORDER BY quality DESC;

-- Recent signals
SELECT signal_type, severity, COUNT(*)
FROM system_alerts
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY signal_type, severity;
```

## 💰 Cost Estimate

**Monthly costs for 144 cycles/day:**
- Bedrock Agent: $50-100
- Lambda: $5-10
- PostgreSQL RDS: $15-50
- **Total: $70-160/month**

## 🔧 Customization

### Adjust Learning Parameters
```python
agent = MarketHunterAgent(
    bedrock_agent_id="...",
    learning_rate=0.15,      # Higher = faster adaptation
    exploration_rate=0.3     # Higher = more exploration
)
```

### Add New Data Source
1. Add to `DATA_SOURCES` list in `market_hunter_agent.py`
2. Create table in `database.py`
3. Add Lambda function
4. Update `action-group-schema.json`
5. Update agent instructions

### Modify Volatility Thresholds
```python
# In assess_market_context()
if abs(price_change) > 7:  # Was 5
    volatility = Volatility.HIGH
```

## 🐛 Troubleshooting

### Issue: "Agent not found"
**Solution:** Check agent ID and alias ID are correct
```bash
aws bedrock-agent list-agents
```

### Issue: "Lambda timeout"
**Solution:** Increase Lambda timeout to 30 seconds
```bash
aws lambda update-function-configuration \
  --function-name market-hunter-actions \
  --timeout 30
```

### Issue: "Database connection failed"
**Solution:** Check security groups allow inbound on port 5432
```bash
aws ec2 describe-security-groups --group-ids sg-xxx
```

## 📚 Learn More

- **Full Documentation:** `README.md`
- **Architecture Details:** `docs/ARCHITECTURE.md`
- **Visual Diagrams:** `docs/MERMAID_DIAGRAMS.md`
- **Implementation Notes:** `IMPLEMENTATION_SUMMARY.md`
- **AWS Setup Guide:** `src/bedrock_agent_setup.py`

## 🎯 Success Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] AWS credentials configured (`aws configure`)
- [ ] Bedrock Agent created in AWS Console
- [ ] Lambda functions deployed (8 functions)
- [ ] Database initialized (PostgreSQL)
- [ ] `.env` file configured
- [ ] Example usage runs successfully
- [ ] Diagrams viewable in VS Code or GitHub
- [ ] Production service deployed
- [ ] Monitoring set up (CloudWatch)

## 🚦 Current Status

✅ **Complete:** Core agent logic, Bedrock integration, database schema, documentation, diagrams
⏳ **Next:** Create actual Bedrock Agent in AWS, deploy Lambda functions, connect real APIs

**Estimated Setup Time:** 2-3 hours for full deployment

---

## 🎉 You're Ready!

Your autonomous market intelligence agent is ready to deploy. Start with:

```bash
# 1. View the diagrams
code docs/MERMAID_DIAGRAMS.md

# 2. Review the architecture
cat docs/ARCHITECTURE.md

# 3. Read the implementation summary
cat IMPLEMENTATION_SUMMARY.md

# 4. Test locally
python src/example_usage.py
```

**Built with ❤️ using Amazon Bedrock AgentCore**

Need help? Check the docs or open an issue on GitHub!
