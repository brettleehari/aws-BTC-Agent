# Phase 1 Validation Checklist

Use this checklist to verify that Phase 1 is working correctly before proceeding to integration.

## ✅ Pre-Flight Checklist

### 1. Files Created

- [ ] `src/memory/enums.py` exists
- [ ] `src/memory/models.py` exists
- [ ] `src/memory/aws_clients.py` exists
- [ ] `src/memory/memory_manager.py` exists
- [ ] `src/memory/decision_logger.py` exists
- [ ] `src/memory/__init__.py` exists
- [ ] `src/memory/requirements.txt` exists
- [ ] `deployment/dynamodb_setup.py` exists
- [ ] `tests/test_memory/test_models.py` exists
- [ ] `tests/test_memory/test_integration.py` exists

**Command to verify:**
```bash
ls -la src/memory/
ls -la deployment/
ls -la tests/test_memory/
```

---

### 2. Dependencies Installed

- [ ] boto3 installed
- [ ] pydantic installed
- [ ] pytest installed
- [ ] pytest-asyncio installed

**Command to verify:**
```bash
pip list | grep -E "boto3|pydantic|pytest"
```

**Expected output:**
```
boto3           1.28.x
pydantic        2.5.x
pytest          7.4.x
pytest-asyncio  0.21.x
```

---

### 3. AWS Configuration

Choose one:

#### Option A: AWS Cloud
- [ ] AWS credentials configured (`aws configure`)
- [ ] Can access AWS (`aws sts get-caller-identity`)
- [ ] Have DynamoDB permissions

**Command to verify:**
```bash
aws sts get-caller-identity
aws dynamodb list-tables
```

#### Option B: Local DynamoDB
- [ ] DynamoDB Local running on port 8000
- [ ] Can connect to localhost:8000

**Command to verify:**
```bash
curl http://localhost:8000
# or
docker ps | grep dynamodb
```

---

### 4. Tables Created

- [ ] `agent_decisions` table exists
- [ ] `agent_memory_ltm` table exists
- [ ] `agent_state` table exists
- [ ] `agent_signals` table exists
- [ ] All tables are ACTIVE

**Command to create:**
```bash
# For AWS
python deployment/dynamodb_setup.py create

# For local
python deployment/dynamodb_setup.py create --local
```

**Command to verify:**
```bash
python deployment/dynamodb_setup.py status
```

**Expected output:**
```
📋 agent_decisions:
   Status: ACTIVE
   GSIs: 3

📋 agent_memory_ltm:
   Status: ACTIVE
   GSIs: 3

📋 agent_state:
   Status: ACTIVE
   GSIs: 2

📋 agent_signals:
   Status: ACTIVE
   GSIs: 3
```

---

### 5. Unit Tests Pass

- [ ] All model tests pass (11 tests)
- [ ] DecisionRecord conversion works
- [ ] MemoryPattern conversion works
- [ ] AgentState conversion works
- [ ] AgentSignal conversion works

**Command to run:**
```bash
pytest tests/test_memory/test_models.py -v
```

**Expected output:**
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

============= 11 passed in X.XXs =============
```

---

### 6. Integration Tests Pass

- [ ] Decision lifecycle test passes
- [ ] Pattern storage test passes
- [ ] STM/LTM separation test passes
- [ ] Agent state test passes
- [ ] Signal publishing test passes
- [ ] Multi-agent test passes

**Command to run:**
```bash
python tests/test_memory/test_integration.py
```

**Expected output:**
```
============================================================
Memory System Integration Tests
============================================================

🧪 Running: Decision Lifecycle
✅ Logged decision: dec-...
✅ Retrieved decision: dec-...
✅ Updated decision with outcome
✅ Queried 1 recent decisions
✅ PASSED: Decision Lifecycle

🧪 Running: Pattern Storage
✅ Stored pattern: pattern-test-...
✅ Retrieved pattern: pattern-test-...
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
✅ Published signal: sig-...
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

### 7. Basic Operations Work

Test basic functionality manually:

```python
# test_manual.py
import asyncio
from datetime import datetime, timezone
from src.memory import DecisionLogger
from src.memory.models import DecisionContext, DecisionReasoning
from src.memory.enums import DecisionType

async def test():
    logger = DecisionLogger()
    
    # 1. Log a decision
    decision_id = await logger.log_decision(
        agent_id="test-agent",
        decision_type=DecisionType.SOURCE_SELECTION,
        decision_made="Test decision",
        context=DecisionContext(
            market_conditions={},
            agent_state={},
            available_resources=[]
        ),
        reasoning=DecisionReasoning(
            confidence_score=0.8,
            alternative_options=[],
            risk_assessment={}
        )
    )
    print(f"✅ Logged: {decision_id}")
    
    # 2. Retrieve it
    decision = await logger.get_decision(decision_id)
    print(f"✅ Retrieved: {decision.decision_id}")
    
    # 3. Query it
    recent = await logger.query_decisions(agent_id="test-agent")
    print(f"✅ Queried: {len(recent)} decisions")

asyncio.run(test())
```

**Run it:**
```bash
python test_manual.py
```

**Expected output:**
```
✅ Logged: dec-1234567890.123456
✅ Retrieved: dec-1234567890.123456
✅ Queried: 1 decisions
```

- [ ] Can log decisions
- [ ] Can retrieve decisions
- [ ] Can query decisions

---

### 8. Documentation Accessible

- [ ] Can open `docs/memory/PHASE1_SETUP.md`
- [ ] Can open `docs/memory/GAP_ANALYSIS.md`
- [ ] Can open `docs/memory/PHASE1_COMPLETE.md`
- [ ] Can open `src/memory/README.md`

**Command to verify:**
```bash
ls -la docs/memory/
```

---

## 🎯 Success Criteria

**Phase 1 is complete if ALL boxes are checked above.**

If any box is unchecked:
1. Review the section
2. Run the verification command
3. Fix any issues
4. Re-check the box

---

## 🚨 Common Issues

### Issue: Import errors
```
ModuleNotFoundError: No module named 'src.memory'
```

**Fix:**
```bash
cd /workspaces/aws-BTC-Agent
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
# or
pip install -e .
```

---

### Issue: AWS credentials not found
```
NoCredentialsError: Unable to locate credentials
```

**Fix:**
```bash
aws configure
# OR
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
```

---

### Issue: Tables don't exist
```
ResourceNotFoundException: Requested resource not found
```

**Fix:**
```bash
python deployment/dynamodb_setup.py create
```

---

### Issue: Local DynamoDB not running
```
EndpointConnectionError: Could not connect to localhost:8000
```

**Fix:**
```bash
docker run -p 8000:8000 amazon/dynamodb-local
```

---

### Issue: Tests fail with async errors
```
RuntimeError: Event loop is closed
```

**Fix:**
```bash
pip install pytest-asyncio
# Ensure tests use @pytest.mark.asyncio
```

---

## ✅ Final Validation

Once all boxes are checked, run this final validation:

```bash
# 1. Check file count
ls src/memory/*.py | wc -l
# Should be 6 files

# 2. Check table status
python deployment/dynamodb_setup.py status
# All 4 tables should be ACTIVE

# 3. Run all tests
pytest tests/test_memory/test_models.py -v && \
python tests/test_memory/test_integration.py
# Should show: 11 passed, 6 passed

# 4. Verify imports work
python -c "from src.memory import DecisionLogger, MemoryManager; print('✅ Imports work')"
```

---

## 🎉 You're Ready!

If all checks pass, **Phase 1 is complete** and you're ready to:

1. ✅ Integrate with Market Hunter Agent
2. ✅ Log real decisions
3. ✅ Store patterns
4. ✅ Track agent state
5. ✅ Publish signals

**Next:** See `docs/memory/PHASE1_COMPLETE.md` for next steps!
