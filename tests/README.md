# Test Suite for Market Hunter Agent

Comprehensive test and evaluation framework for the Market Hunter Agent using Amazon Bedrock AgentCore.

## 📋 Overview

This test suite includes:
- **Unit Tests**: Test individual components and algorithms
- **Integration Tests**: Test Bedrock Agent invocation and AWS services
- **Evaluation Framework**: Comprehensive performance evaluation

## 🗂️ Test Files

```
tests/
├── __init__.py                  # Package initialization
├── test_agent_core.py          # Unit tests for agent core logic
├── test_llm_router.py          # Unit tests for LLM router
├── test_integration.py         # Integration tests with Bedrock
├── test_evaluations.py         # Evaluation framework
├── run_tests.py                # Test runner
└── README.md                   # This file
```

## 🚀 Quick Start

### Run All Tests
```bash
cd /workspaces/aws-BTC-Agent
python tests/run_tests.py --all
```

### Run Specific Test Suites
```bash
# Unit tests only (no AWS required)
python tests/run_tests.py --unit

# Integration tests only (requires AWS)
python tests/run_tests.py --integration

# Evaluations only
python tests/run_tests.py --eval
```

### Run Individual Test Files
```bash
# Using pytest
pytest tests/test_agent_core.py -v
pytest tests/test_llm_router.py -v

# Using unittest
python -m unittest tests.test_agent_core -v
python -m unittest tests.test_llm_router -v
```

## 📦 Installation

### Install Test Dependencies
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Set Environment Variables
```bash
# For integration tests
export BEDROCK_AGENT_ID="your-agent-id"
export BEDROCK_AGENT_ALIAS_ID="your-alias-id"
export AWS_REGION="us-east-1"

# For database tests (optional)
export DB_HOST="your-db-host"
export DB_NAME="market_hunter"
export DB_USER="your-user"
export DB_PASSWORD="your-password"
```

## 🧪 Unit Tests

### test_agent_core.py

Tests core agent functionality without AWS dependencies:

#### TestMarketContextAssessment
- ✅ `test_high_volatility_detection`: Detects high volatility (>5%)
- ✅ `test_low_volatility_detection`: Detects low volatility (<2%)
- ✅ `test_trend_detection`: Classifies bullish/bearish/sideways
- ✅ `test_trading_session_detection`: Identifies Asian/EU/US sessions

#### TestSourceSelection
- ✅ `test_high_volatility_selects_more_sources`: Selects 5-6 sources in high vol
- ✅ `test_low_volatility_selects_fewer_sources`: Selects 3-4 sources in low vol
- ✅ `test_source_scoring_considers_context`: Adapts to market conditions
- ✅ `test_exploration_introduces_randomness`: Exploration creates variation

#### TestAdaptiveLearning
- ✅ `test_metric_update_increases_on_success`: Metrics improve on success
- ✅ `test_metric_update_decreases_on_failure`: Metrics decrease on failure
- ✅ `test_ema_learning_rate`: Exponential moving average calculation

#### TestBedrockAgentInvocation
- ✅ `test_agent_invocation_success`: Mocked Bedrock invocation
- ✅ `test_agent_invocation_handles_errors`: Error handling

#### TestSignalGeneration
- ✅ `test_whale_activity_signal_generation`: Whale signals
- ✅ `test_sentiment_signal_generation`: Sentiment signals
- ✅ `test_multiple_signals_from_different_sources`: Multiple signals

**Run**: `python -m unittest tests.test_agent_core -v`

---

### test_llm_router.py

Tests LLM router functionality:

#### TestModelRegistry
- ✅ `test_registry_has_10_models`: Registry contains 10 models
- ✅ `test_get_model_by_id`: Retrieve model by ID
- ✅ `test_get_models_by_capability`: Filter by capability level
- ✅ `test_get_models_by_provider`: Filter by provider
- ✅ `test_get_models_by_region`: Filter by AWS region

#### TestModelSelection
- ✅ `test_simple_task_selects_cheap_model`: Simple → cheap model
- ✅ `test_complex_task_selects_advanced_model`: Complex → advanced model
- ✅ `test_expert_capability_filters_correctly`: Expert filtering
- ✅ `test_cost_constraint_filters_expensive_models`: Budget constraints
- ✅ `test_provider_preference_prioritizes_provider`: Provider preference
- ✅ `test_long_context_selects_large_context_window`: Context window

#### TestScoringAlgorithm
- ✅ `test_capability_score_calculation`: Capability scoring
- ✅ `test_cost_efficiency_bonus`: Cost efficiency bonus
- ✅ `test_speed_score_calculation`: Speed scoring
- ✅ `test_reasoning_score_for_complex_tasks`: Reasoning weight

#### TestUsageTracking
- ✅ `test_usage_tracking_records_invocation`: Track invocations
- ✅ `test_usage_report_structure`: Report structure
- ✅ `test_reset_usage_tracking`: Reset tracking

**Run**: `python -m unittest tests.test_llm_router -v`

---

## 🔗 Integration Tests

### test_integration.py

Tests with real AWS services (requires credentials):

#### TestBedrockAgentIntegration
- ✅ `test_bedrock_agent_invoke`: Real Bedrock invocation
- ✅ `test_action_group_invocation`: Action group execution
- ✅ `test_full_cycle_execution`: Complete agent cycle
- ✅ `test_multiple_source_queries`: Query multiple sources

#### TestBedrockAgentWithRouter
- ✅ `test_router_selects_different_models`: Dynamic model selection
- ✅ `test_cost_tracking_accuracy`: Cost tracking validation

#### TestDatabaseIntegration
- ✅ `test_store_execution_record`: Store executions
- ✅ `test_store_and_retrieve_metrics`: Metrics storage
- ✅ `test_store_signals`: Signal storage

#### TestEndToEndFlow
- ✅ `test_complete_agent_workflow`: Full E2E workflow

**Run**: `python -m unittest tests.test_integration -v`

**Requirements**:
```bash
export BEDROCK_AGENT_ID="your-agent-id"
export BEDROCK_AGENT_ALIAS_ID="your-alias-id"
export DB_HOST="your-db-host"
export DB_NAME="market_hunter"
export DB_USER="your-user"
export DB_PASSWORD="your-password"
```

---

## 📊 Evaluation Framework

### test_evaluations.py

Comprehensive agent performance evaluation:

#### Evaluation Scenarios
1. **High Volatility Bullish**: Tests high volatility + bullish trend
2. **High Volatility Bearish**: Tests high volatility + bearish trend
3. **Low Volatility Sideways**: Tests low volatility + sideways market
4. **Medium Volatility Breakout**: Tests breakout detection
5. **Extreme Fear**: Tests extreme fear detection
6. **Extreme Greed**: Tests extreme greed detection

#### Metrics Evaluated
- **Decision Quality**:
  - Source selection accuracy
  - Exploration/exploitation balance
  - Learning effectiveness
  
- **Performance**:
  - Average execution time
  - Success rate
  - Signal quality score
  
- **Cost Efficiency**:
  - Cost per cycle
  - Cost per signal
  - ROI estimate
  
- **Bedrock-Specific**:
  - Invocation success rate
  - Average latency
  - Error rate

#### Running Evaluations
```bash
# Run full evaluation
python tests/test_evaluations.py

# With custom agent
python tests/test_evaluations.py --agent-id YOUR_ID --alias-id YOUR_ALIAS

# With LLM router enabled
python tests/test_evaluations.py --use-router

# Export results
python tests/test_evaluations.py --export results.json
```

#### Evaluation Output
```
🧪 Evaluating: High Volatility Bullish
   High volatility with bullish trend - should query 5-6 sources
   ✅ Success
   Source Accuracy: 85.00%
   Signal Quality: 90.00%
   Execution Time: 2.35s

📊 EVALUATION SUMMARY
════════════════════════════════════════════════════════════════
🎯 Decision Quality
   Source Selection Accuracy: 85.50%
   Signal Quality Score:      88.20%
   Exploration Balance:       75.30%
   Learning Effectiveness:    82.00%

⚡ Performance
   Success Rate:              100.00%
   Avg Execution Time:        2.45s
   Bedrock Invocation Rate:   100.00%
   Bedrock Avg Latency:       2.45s
   Bedrock Error Rate:        0.00%

💰 Cost Efficiency
   Cost per Cycle:            $0.0234
   Cost per Signal:           $0.0078

🏆 Overall Grade
   Overall Score: 85.67% - A (Very Good)
```

---

## 📈 Coverage

### Generate Coverage Report
```bash
# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Target Coverage
- **Agent Core**: >90%
- **LLM Router**: >85%
- **Integration**: >70%

---

## 🎯 Test Scenarios

### Market Contexts Tested
| Context | Volatility | Trend | Expected Behavior |
|---------|-----------|-------|-------------------|
| Bull Run | High (>5%) | Bullish | Query 5-6 sources, prioritize whales/institutional |
| Bear Market | High (>5%) | Bearish | Query 5-6 sources, prioritize derivatives/risk |
| Sideways | Low (<2%) | Sideways | Query 3-4 sources, explore narratives |
| Breakout | Medium (3-5%) | Bullish | Query 4-5 sources, technical breakouts |
| Extreme Fear | Very High | Bearish | Detect fear, risk signals |
| Extreme Greed | High | Bullish | Detect greed, sentiment signals |

### Data Sources Tested
- ✅ Whale Movements
- ✅ Narrative Shifts
- ✅ Arbitrage Opportunities
- ✅ Influencer Signals
- ✅ Technical Breakouts
- ✅ Institutional Flows
- ✅ Derivatives Signals
- ✅ Macro Signals

### Signal Types Tested
- ✅ WHALE_ACTIVITY
- ✅ POSITIVE_NARRATIVE
- ✅ INSTITUTIONAL_ACCUMULATION
- ✅ EXTREME_FUNDING
- ✅ EXTREME_FEAR
- ✅ EXTREME_GREED
- ✅ TECHNICAL_BREAKOUT

---

## 🐛 Troubleshooting

### Common Issues

#### "No module named 'market_hunter_agent'"
```bash
# Add src to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/workspaces/aws-BTC-Agent/src"
```

#### "Bedrock Agent not found"
```bash
# Verify environment variables
echo $BEDROCK_AGENT_ID
echo $BEDROCK_AGENT_ALIAS_ID

# Check AWS credentials
aws sts get-caller-identity
```

#### "Database connection failed"
```bash
# Test database connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME
```

#### "Test takes too long"
```bash
# Run specific test
pytest tests/test_agent_core.py::TestMarketContextAssessment::test_high_volatility_detection

# Skip slow tests
pytest -m "not slow"
```

---

## 📝 Writing New Tests

### Unit Test Template
```python
import unittest
from market_hunter_agent import MarketHunterAgent

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.agent = MarketHunterAgent(
            bedrock_agent_id="test-agent",
            bedrock_agent_alias_id="test-alias"
        )
    
    def test_feature(self):
        # Arrange
        input_data = {...}
        
        # Act
        result = self.agent.some_method(input_data)
        
        # Assert
        self.assertEqual(result, expected_value)
```

### Integration Test Template
```python
import unittest
import os

class TestNewIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent_id = os.getenv('BEDROCK_AGENT_ID')
        if not cls.agent_id:
            raise unittest.SkipTest("Set BEDROCK_AGENT_ID")
    
    def test_integration(self):
        # Test with real AWS services
        pass
```

---

## 🎓 Best Practices

1. **Run unit tests frequently** during development
2. **Run integration tests** before commits
3. **Run evaluations** before releases
4. **Mock external services** in unit tests
5. **Use real services** in integration tests
6. **Document test scenarios** clearly
7. **Keep tests independent** (no shared state)
8. **Use descriptive test names** (test_what_when_expected)

---

## 📊 Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt pytest
      - name: Run unit tests
        run: pytest tests/ -v --ignore=tests/test_integration.py
```

---

## 📚 References

- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/)
- [pytest Documentation](https://docs.pytest.org/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## ✅ Test Checklist

Before deployment:
- [ ] All unit tests pass
- [ ] Integration tests pass with real Bedrock
- [ ] Evaluation score > 80%
- [ ] Code coverage > 85%
- [ ] No critical bugs
- [ ] Performance benchmarks met
- [ ] Cost optimization validated

---

**Last Updated**: 2024  
**Test Suite Version**: 1.0.0  
**Compatible with**: Market Hunter Agent v2.0 (with LLM Router)
