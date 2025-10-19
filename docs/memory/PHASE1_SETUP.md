# Phase 1 Setup and Validation Guide

## Quick Start

This guide will help you set up and validate the Phase 1 memory system foundation.

---

## Prerequisites

1. **Python 3.9+** installed
2. **AWS Account** with credentials configured
3. **boto3** and dependencies installed

```bash
pip install -r src/memory/requirements.txt
```

---

## Step 1: Install Dependencies

```bash
cd /workspaces/aws-BTC-Agent
pip install boto3 pydantic pytest pytest-asyncio
```

---

## Step 2: Configure AWS Credentials

### Option A: AWS Credentials File
```bash
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
```

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Option C: Local DynamoDB (for testing)
```bash
# Install and run DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local
```

---

## Step 3: Create DynamoDB Tables

### For AWS DynamoDB
```bash
python deployment/dynamodb_setup.py create
```

### For Local DynamoDB
```bash
python deployment/dynamodb_setup.py create --local
```

**Expected Output:**
```
============================================================
Creating DynamoDB Tables for Memory System
============================================================

📋 Creating table: agent_decisions...
✅ Table 'agent_decisions' created successfully

📋 Creating table: agent_memory_ltm...
✅ Table 'agent_memory_ltm' created successfully

📋 Creating table: agent_state...
✅ Table 'agent_state' created successfully

📋 Creating table: agent_signals...
✅ Table 'agent_signals' created successfully

⏳ Waiting for tables to become active...
✅ All tables are now active!

============================================================
✅ Table creation complete!
============================================================
```

---

## Step 4: Verify Table Status

```bash
python deployment/dynamodb_setup.py status
```

**Expected Output:**
```
============================================================
Memory System Tables Status
============================================================

📋 agent_decisions:
   Status: ACTIVE
   Items: 0
   Size: 0 bytes
   GSIs: 3
   Created: 2025-10-18 12:00:00

📋 agent_memory_ltm:
   Status: ACTIVE
   Items: 0
   Size: 0 bytes
   GSIs: 3
   Created: 2025-10-18 12:00:00

📋 agent_state:
   Status: ACTIVE
   Items: 0
   Size: 0 bytes
   GSIs: 2
   Created: 2025-10-18 12:00:00

📋 agent_signals:
   Status: ACTIVE
   Items: 0
   Size: 0 bytes
   GSIs: 3
   Created: 2025-10-18 12:00:00
```

---

## Step 5: Run Unit Tests

Test the data models and DynamoDB conversion:

```bash
cd /workspaces/aws-BTC-Agent
pytest tests/test_memory/test_models.py -v
```

**Expected Output:**
```
tests/test_memory/test_models.py::TestDecisionRecord::test_decision_record_creation PASSED
tests/test_memory/test_models.py::TestDecisionRecord::test_decision_with_outcome PASSED
tests/test_memory/test_models.py::TestDecisionRecord::test_decision_dynamodb_conversion PASSED
tests/test_memory/test_models.py::TestMemoryPattern::test_pattern_creation PASSED
tests/test_memory/test_models.py::TestMemoryPattern::test_pattern_metadata PASSED
tests/test_memory/test_models.py::TestMemoryPattern::test_pattern_dynamodb_conversion PASSED
tests/test_memory/test_models.py::TestAgentState::test_agent_state_creation PASSED
tests/test_memory/test_models.py::TestAgentState::test_agent_state_dynamodb_conversion PASSED
tests/test_memory/test_models.py::TestAgentSignal::test_signal_creation PASSED
tests/test_memory/test_models.py::TestAgentSignal::test_signal_with_response PASSED
tests/test_memory/test_models.py::TestAgentSignal::test_signal_dynamodb_conversion PASSED

============= 11 passed in 2.34s =============
```

---

## Step 6: Run Integration Tests

Test end-to-end memory operations:

```bash
python tests/test_memory/test_integration.py
```

**Expected Output:**
```
============================================================
Memory System Integration Tests
============================================================

🧪 Running: Decision Lifecycle
✅ Logged decision: dec-1234567890
✅ Retrieved decision: dec-1234567890
✅ Updated decision with outcome
✅ Queried 1 recent decisions
✅ PASSED: Decision Lifecycle

🧪 Running: Pattern Storage
✅ Stored pattern: pattern-test-1234567890
✅ Retrieved pattern: pattern-test-1234567890
✅ Updated pattern confidence to 0.85
✅ Queried 1 patterns
✅ PASSED: Pattern Storage

🧪 Running: STM/LTM Separation
✅ STM query returned 1 recent decisions
✅ Full query returned 2 total decisions
✅ PASSED: STM/LTM Separation

🧪 Running: Agent State
✅ Saved agent state
✅ Retrieved agent state
✅ Updated agent state
✅ PASSED: Agent State

🧪 Running: Signal Publishing
✅ Published signal: sig-1234567890
✅ Retrieved 1 signals for target agent
✅ Updated signal processing status
✅ PASSED: Signal Publishing

🧪 Running: Multi-Agent
✅ Created decisions for 3 agents
✅ Verified agent-specific decision queries
✅ PASSED: Multi-Agent

============================================================
Test Results: 6 passed, 0 failed
============================================================
```

---

## Step 7: Test Basic Operations

Create a test script to validate basic operations:

```python
# test_basic_operations.py
import asyncio
from datetime import datetime, timezone
from src.memory.decision_logger import DecisionLogger
from src.memory.models import DecisionContext, DecisionReasoning, DecisionOutcome
from src.memory.enums import DecisionType

async def test_basic_operations():
    logger = DecisionLogger()
    
    # Log a decision
    context = DecisionContext(
        market_conditions={"btc_price": 45000},
        agent_state={"status": "active"},
        available_resources=["source1"]
    )
    
    reasoning = DecisionReasoning(
        confidence_score=0.85,
        alternative_options=["option2"],
        risk_assessment={"level": "medium"}
    )
    
    decision_id = await logger.log_decision(
        agent_id="test-agent",
        decision_type=DecisionType.SOURCE_SELECTION,
        decision_made="Selected source1",
        context=context,
        reasoning=reasoning
    )
    
    print(f"✅ Logged decision: {decision_id}")
    
    # Retrieve decision
    decision = await logger.get_decision(decision_id)
    print(f"✅ Retrieved decision: {decision.decision_id}")
    print(f"   Agent: {decision.agent_id}")
    print(f"   Type: {decision.decision_type}")
    print(f"   Confidence: {decision.reasoning.confidence_score}")
    
    # Update with outcome
    outcome = DecisionOutcome(
        success=True,
        actual_result={"quality": 0.9},
        execution_time_ms=120,
        metrics={"accuracy": 0.92}
    )
    
    await logger.log_outcome(decision_id, outcome)
    print(f"✅ Updated with outcome")
    
    # Query recent decisions
    recent = await logger.query_decisions(
        agent_id="test-agent"
    )
    print(f"✅ Found {len(recent)} recent decisions")

if __name__ == '__main__':
    asyncio.run(test_basic_operations())
```

Run it:
```bash
python test_basic_operations.py
```

---

## Troubleshooting

### Issue: Tables already exist
**Solution:** Delete and recreate
```bash
python deployment/dynamodb_setup.py delete
python deployment/dynamodb_setup.py create
```

### Issue: AWS credentials not found
**Solution:** Run `aws configure` or set environment variables

### Issue: Permission denied errors
**Solution:** Ensure your AWS user has DynamoDB permissions:
- `dynamodb:CreateTable`
- `dynamodb:DescribeTable`
- `dynamodb:PutItem`
- `dynamodb:GetItem`
- `dynamodb:Query`
- `dynamodb:UpdateItem`

### Issue: Connection timeout
**Solution:** Check region setting and network connectivity

### Issue: Import errors
**Solution:** Install dependencies:
```bash
pip install boto3 pydantic pytest pytest-asyncio
```

---

## What's Working Now ✅

After completing these steps, you have:

1. ✅ **4 DynamoDB Tables** - All tables created with proper schemas and GSIs
2. ✅ **Data Models** - Pydantic models with validation and DynamoDB conversion
3. ✅ **Memory Manager** - Full CRUD operations for decisions, patterns, state, signals
4. ✅ **Decision Logger** - High-level API for logging decisions and outcomes
5. ✅ **Multi-Agent Support** - All operations support multiple agents via agent_id
6. ✅ **STM/LTM Queries** - Time-based queries for short-term and long-term memory
7. ✅ **Unit Tests** - Comprehensive tests for all models
8. ✅ **Integration Tests** - End-to-end validation of memory operations

---

## What's Next

### Phase 2: Integration with Market Hunter Agent
- Add decision logging to existing agent code
- Log decisions at all decision points
- Test with real agent cycles

### Phase 3: Multi-Agent Coordinator (Optional)
- Implement agent registry
- Add signal orchestration
- Enable cross-agent communication

### Phase 4: Pattern Learning (Optional)
- Implement automatic pattern identification
- Add STM → LTM consolidation
- Enable pattern evolution

---

## Cost Monitoring

Monitor your AWS costs:

```bash
# Check table status and sizes
python deployment/dynamodb_setup.py status
```

**Expected Costs:**
- **On-Demand Pricing**: ~$3.50/month for demo usage
- **First 25 GB storage**: Free
- **First 2.5M reads/month**: Free (first 12 months)

---

## Cleanup

To delete all tables and stop incurring costs:

```bash
python deployment/dynamodb_setup.py delete
```

**⚠️ Warning:** This will permanently delete all data!

---

## Support

If you encounter issues:

1. Check AWS CloudWatch logs for errors
2. Verify table status: `python deployment/dynamodb_setup.py status`
3. Review error messages in terminal output
4. Ensure all dependencies are installed

---

## Summary

You now have a **fully functional Phase 1 memory system** with:
- ✅ Persistent storage in DynamoDB
- ✅ Decision logging with context and outcomes
- ✅ Pattern storage and retrieval
- ✅ Agent state management
- ✅ Signal publishing between agents
- ✅ Multi-agent support
- ✅ Comprehensive testing

**Ready to integrate with your agents!** 🚀
