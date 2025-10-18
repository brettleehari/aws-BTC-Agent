# 🧪 Testing & Goal Alignment Guide

Complete guide for testing the Market Hunter Agent and ensuring codebase alignment with project goals.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Goal Alignment Tests](#goal-alignment-tests)
3. [Test Types](#test-types)
4. [Running Tests](#running-tests)
5. [Git Workflow Integration](#git-workflow-integration)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Writing Tests](#writing-tests)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Market Hunter Agent uses a **goal-driven testing approach** that continuously validates the codebase against core architectural principles:

### Why Goal Alignment Tests?

Traditional tests check if code *works*. Goal alignment tests check if code *aligns with architecture*.

**Example**: A hardcoded list of data sources would pass unit tests but fail goal alignment tests because it violates autonomous decision-making principles.

### 10 Core Goals

1. **Autonomous Decision-Making** - Agent decides dynamically, not hardcoded
2. **Cost Optimization** - Intelligent LLM routing saves money
3. **Learning & Adaptation** - System learns from experience
4. **Real-Time Performance** - Fast enough for live trading (<60s)
5. **Signal Quality** - High-quality, actionable signals
6. **Data Source Diversity** - Uses 8+ different data sources
7. **Clean Architecture** - Well-organized, maintainable code
8. **Comprehensive Testing** - Proper test coverage
9. **Documentation** - Well-documented codebase
10. **Production Readiness** - Ready for deployment

---

## 🎯 Goal Alignment Tests

### What They Test

```python
# ✗ BAD - Fails goal alignment (hardcoded)
def select_sources():
    return ["whale_movements", "narrative_shifts", "derivatives"]

# ✓ GOOD - Passes goal alignment (dynamic)
def select_sources(volatility, trend, performance_history):
    if volatility > 0.05:
        num_sources = 6
    else:
        num_sources = 3
    
    # Score sources based on current conditions
    scores = calculate_source_scores(trend, performance_history)
    return top_k_sources(scores, num_sources)
```

### Test Structure

**10 Test Classes**, one per goal:

```python
class TestGoal1_Autonomy(unittest.TestCase):
    """Goal 1: Agent makes autonomous decisions"""
    
    def test_no_hardcoded_source_selection(self):
        """Verify agent doesn't hardcode which sources to query"""
        # Checks code for bad patterns
    
    def test_decision_uses_context(self):
        """Verify decisions are based on market context"""
        # Ensures volatility, trend used in decisions
    
    def test_exploration_mechanism_exists(self):
        """Verify agent has exploration mechanism"""
        # Checks for exploration logic
```

### Running Goal Alignment Tests

```bash
# Primary method
make test-goals

# Direct execution
python tests/test_goal_alignment.py

# Part of full test suite
make test

# With verbose output
python tests/test_goal_alignment.py -v
```

### Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOAL ALIGNMENT TESTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Verifying codebase alignment with project goals:
1. ✓ Autonomous decision-making
2. ✓ Cost optimization
3. ✓ Learning and adaptation
4. ✓ Real-time performance
5. ✓ Signal quality
6. ✓ Data source diversity
7. ✓ Clean architecture
8. ✓ Comprehensive testing
9. ✓ Documentation
10. ✓ Production readiness

test_no_hardcoded_source_selection (__main__.TestGoal1_Autonomy) ... ok
test_decision_uses_context (__main__.TestGoal1_Autonomy) ... ok
test_exploration_mechanism_exists (__main__.TestGoal1_Autonomy) ... ok
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Tests: 45
✓ Passed: 42
✗ Failed: 2
⚠ Errors: 0
○ Skipped: 1

Overall: SUCCESS ✓
```

---

## 🧪 Test Types

### 1. Goal Alignment Tests ⭐

**Purpose**: Validate architectural alignment

**Location**: `tests/test_goal_alignment.py`

**Run**: `make test-goals`

**Speed**: Fast (< 10 seconds)

**AWS Required**: No

**When to Run**: 
- Before every commit
- When changing core algorithms
- During code reviews

### 2. Unit Tests

**Purpose**: Test individual components

**Location**: `tests/test_agent_core.py`, `tests/test_llm_router.py`

**Run**: `make test-unit`

**Speed**: Fast (< 30 seconds)

**AWS Required**: No

**Coverage**:
- Agent decision logic
- LLM routing algorithms
- Data processing functions
- Performance calculations

### 3. Integration Tests

**Purpose**: Test AWS service integration

**Location**: `tests/test_integration.py`

**Run**: `make test-integration`

**Speed**: Slow (2-5 minutes)

**AWS Required**: Yes

**Tests**:
- Bedrock Agent invocation
- Lambda function execution
- Database operations
- Real API calls

### 4. Evaluation Tests

**Purpose**: Evaluate agent performance

**Location**: `tests/test_evaluations.py`

**Run**: `make test-eval`

**Speed**: Slow (5-10 minutes)

**AWS Required**: Yes

**Metrics**:
- Decision quality
- Cost optimization
- Learning effectiveness
- Signal accuracy

---

## 🚀 Running Tests

### Quick Reference

```bash
# Most important - run before every commit!
make test-goals

# Fast tests (unit + goal alignment)
make test-fast

# All tests (takes 5-10 minutes)
make test

# Specific test types
make test-unit
make test-integration
make test-eval

# With coverage report
make coverage

# Watch mode (re-run on file changes)
make watch-tests
```

### Using Python Directly

```bash
# Goal alignment
python tests/test_goal_alignment.py

# Test runner
python tests/run_tests.py --all
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --eval

# Using pytest
pytest tests/ -v
pytest tests/test_agent_core.py -v
pytest tests/ -k "test_autonomy" -v
```

### Test Selection

```bash
# Run specific test class
pytest tests/test_goal_alignment.py::TestGoal1_Autonomy -v

# Run specific test method
pytest tests/test_goal_alignment.py::TestGoal1_Autonomy::test_no_hardcoded_source_selection -v

# Run tests matching pattern
pytest tests/ -k "cost" -v
pytest tests/ -k "not slow" -v

# Stop on first failure
pytest tests/ -x

# Show print statements
pytest tests/ -s
```

---

## 🔄 Git Workflow Integration

### Pre-Commit Hooks

When you run `git commit`, the following checks run **automatically**:

1. ✅ **Goal Alignment Tests** - Ensures architectural alignment
2. ✅ **Fast Unit Tests** - Verifies core functionality
3. ✅ **Syntax Check** - Python syntax validation
4. ✅ **Security Check** - No hardcoded credentials
5. ✅ **File Size Check** - No accidentally large files

### Setup Pre-Commit Hooks

```bash
# Automatic setup (recommended)
./setup-dev-workflow.sh

# Manual setup
chmod +x .git/hooks/pre-commit
pip install pre-commit
pre-commit install
```

### Pre-Commit Hook Flow

```
git commit -m "feat: new feature"
    ↓
🔍 Running pre-commit checks...
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Goal Alignment Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ All 45 tests passed
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Fast Unit Tests
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ 12 tests passed
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Checking for print statements
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ No print statements found
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Checking for hardcoded credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ No hardcoded credentials found
    ↓
✓ All checks passed! Ready to commit.
    ↓
[main abc1234] feat: new feature
```

### Skipping Pre-Commit Hooks

**Not recommended**, but possible:

```bash
# Skip all hooks
git commit --no-verify -m "WIP: debugging"

# Better: Fix issues first
make check  # Run all checks
git commit -m "feat: new feature"
```

### Development Workflow

```bash
# 1. Make changes
vim src/market_hunter_agent.py

# 2. Format code
make format

# 3. Run tests
make test-goals  # Quick check
make test-fast   # More thorough

# 4. Check quality
make lint

# 5. Verify everything
make check  # Runs: format, lint, test-fast, test-goals

# 6. Commit (hooks run automatically)
git add .
git commit -m "feat: add dynamic source selection"

# 7. Push (CI/CD runs on GitHub)
git push
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

When you push to GitHub, automated tests run via GitHub Actions.

**Location**: `.github/workflows/test.yml`

### Pipeline Jobs

```yaml
Workflow: Test & Validate
    ↓
┌─────────────────────────────────────┐
│  Job 1: Goal Alignment Tests ⭐     │
│  - Runs on: Every push/PR           │
│  - Duration: ~10 seconds            │
│  - AWS Required: No                 │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 2: Unit Tests                  │
│  - Runs on: Every push/PR           │
│  - Duration: ~30 seconds            │
│  - AWS Required: No                 │
│  - Generates: Coverage report       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 3: Integration Tests           │
│  - Runs on: Push to main only       │
│  - Duration: ~3 minutes             │
│  - AWS Required: Yes                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 4: Code Quality                │
│  - Black (formatting)               │
│  - isort (import sorting)           │
│  - flake8 (linting)                 │
│  - mypy (type checking)             │
│  - bandit (security)                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 5: Documentation Check         │
│  - README exists                    │
│  - Docs structure valid             │
│  - No broken links                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Job 6: Security Scan               │
│  - Trivy vulnerability scanner      │
│  - Uploads to GitHub Security       │
└─────────────────────────────────────┘
    ↓
    ✓ All checks passed!
```

### Triggering CI/CD

```bash
# Triggers on push to main/develop
git push origin main

# Triggers on pull request
git push origin feature-branch
# Then create PR on GitHub

# Manual trigger
# Go to GitHub Actions → Test & Validate → Run workflow
```

### Viewing Results

1. Go to **GitHub repository**
2. Click **Actions** tab
3. See workflow runs and results
4. Click on run for details

### Setting Up Secrets

For integration tests, add AWS credentials:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`

---

## ✍️ Writing Tests

### Adding Goal Alignment Tests

```python
# tests/test_goal_alignment.py

class TestGoal1_Autonomy(unittest.TestCase):
    """Goal 1: Agent makes autonomous decisions"""
    
    def test_new_autonomy_check(self):
        """Test description"""
        agent_file = Path(__file__).parent.parent / "src" / "market_hunter_agent.py"
        with open(agent_file) as f:
            code = f.read()
        
        # Check for bad patterns
        self.assertNotIn('hardcoded_value', code,
            "Should not have hardcoded values")
        
        # Check for good patterns
        self.assertIn('dynamic_calculation', code,
            "Should use dynamic calculations")
```

### Adding Unit Tests

```python
# tests/test_agent_core.py

import unittest
from market_hunter_agent import MarketHunterAgent

class TestSourceSelection(unittest.TestCase):
    """Test source selection logic"""
    
    def test_high_volatility_selects_more_sources(self):
        """High volatility should select more sources"""
        agent = MarketHunterAgent()
        
        # High volatility scenario
        selected = agent.select_sources(volatility=0.08)
        self.assertGreaterEqual(len(selected), 5)
        
        # Low volatility scenario
        selected = agent.select_sources(volatility=0.01)
        self.assertLessEqual(len(selected), 3)
```

### Test Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** - `test_high_volatility_selects_more_sources`
3. **Clear failure messages** - `self.assertTrue(x, "Should calculate scores")`
4. **Test edge cases** - Empty inputs, extreme values
5. **Mock external services** - Don't call real APIs in unit tests
6. **Use fixtures** - Share test data setup

---

## 🐛 Troubleshooting

### Goal Alignment Tests Failing

**Issue**: Test fails with "Should not have hardcoded values"

**Solution**: 
```python
# ✗ BAD
sources = ["whale_movements", "narrative_shifts"]

# ✓ GOOD  
sources = self.select_sources_dynamically(context)
```

**Issue**: Test fails with "Agent should use 'volatility' in decision-making"

**Solution**: Add volatility to your decision logic:
```python
def decide(self, volatility, trend):
    if volatility > 0.05:
        # High volatility logic
    else:
        # Low volatility logic
```

### Pre-Commit Hook Failing

**Issue**: Hook fails but tests pass locally

**Solution**:
```bash
# Run hook manually to see details
.git/hooks/pre-commit

# Or check specific test
python tests/test_goal_alignment.py -v
```

**Issue**: "Permission denied" when committing

**Solution**:
```bash
chmod +x .git/hooks/pre-commit
```

### CI/CD Failures

**Issue**: Tests pass locally but fail on GitHub

**Solution**:
- Check Python version (CI uses 3.9)
- Check for environment-specific code
- Review GitHub Actions logs

**Issue**: Integration tests failing

**Solution**:
- Verify AWS credentials in GitHub Secrets
- Check AWS service limits
- Review CloudWatch logs

### Import Errors

**Issue**: `ModuleNotFoundError` in tests

**Solution**:
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or use setup script
./setup-dev-workflow.sh
```

---

## 📊 Coverage Reports

### Generating Coverage

```bash
# HTML report
make coverage
# Opens htmlcov/index.html

# Terminal report
pytest tests/ --cov=src --cov-report=term

# XML report (for CI/CD)
pytest tests/ --cov=src --cov-report=xml
```

### Coverage Goals

- **Overall**: > 80%
- **Core Agent**: > 90%
- **LLM Router**: > 85%
- **Database**: > 75%

---

## 🎯 Goal Alignment Criteria Details

### Goal 1: Autonomous Decision-Making

**What to check**:
- No hardcoded source lists
- Decisions use context (volatility, trend, time)
- Has exploration mechanism
- Source count adapts to conditions

**Anti-patterns**:
```python
# ✗ Always query these 3 sources
sources = ["whale", "narrative", "derivatives"]

# ✗ Fixed logic
if True:
    query_whale_movements()
```

**Good patterns**:
```python
# ✓ Dynamic selection
sources = self.score_and_select(context)

# ✓ Context-driven
if context.volatility > threshold:
    query_more_sources()
```

### Goal 2: Cost Optimization

**What to check**:
- LLM router exists and is used
- Multiple models supported (cheap + expensive)
- Task-based model selection
- Cost tracking implemented

**Anti-patterns**:
```python
# ✗ Always use expensive model
model = "claude-3-opus"
```

**Good patterns**:
```python
# ✓ Task-based routing
model = router.select_model(task_type, complexity)
```

### Goal 3: Learning & Adaptation

**What to check**:
- Performance metrics stored
- Historical data influences decisions
- Learning algorithm implemented
- No static weights

**Anti-patterns**:
```python
# ✗ Static weights
whale_weight = 0.8  # Never changes
```

**Good patterns**:
```python
# ✓ Learning algorithm
new_score = (1 - alpha) * old_score + alpha * new_observation
```

### Goal 4: Real-Time Performance

**What to check**:
- Database indexes exist
- No full table scans
- Async operations where possible
- Timeout protection

### Goal 5: Signal Quality

**What to check**:
- Signals have severity levels
- Confidence scores included
- Multiple signal types supported
- Signals stored for analysis

### Goal 6: Data Source Diversity

**What to check**:
- Minimum 8 data sources
- Sources cover different categories
- No single source dominates

### Goal 7: Clean Architecture

**What to check**:
- Separation of concerns (separate modules)
- Configuration externalized
- Error handling exists
- Logging implemented

### Goal 8: Comprehensive Testing

**What to check**:
- Unit tests exist
- Integration tests exist
- Evaluation framework exists

### Goal 9: Documentation

**What to check**:
- README comprehensive (>1000 chars)
- Architecture documented
- Docstrings in main classes

### Goal 10: Production Readiness

**What to check**:
- Environment variables used (no hardcoded secrets)
- Deployment scripts exist
- requirements.txt exists
- CI/CD configured

---

## 🎉 Summary

### Daily Workflow

```bash
# Morning: Start development
./setup-dev-workflow.sh  # First time only

# During development
make format              # Format code
make test-goals          # Quick alignment check

# Before commit
make check              # Full pre-commit check

# Commit (hooks run automatically)
git commit -m "feat: new feature"

# Push (CI/CD runs on GitHub)
git push
```

### Key Takeaways

1. **Goal alignment tests are the most important** - They ensure architectural integrity
2. **Run tests before every commit** - Pre-commit hooks do this automatically
3. **Use `make` commands** - They're simpler and consistent
4. **Check CI/CD results** - GitHub Actions shows full test results
5. **Fix failures immediately** - Don't let them accumulate

---

## 📞 Support

- **Quick Start**: [QUICKSTART_DEV.md](QUICKSTART_DEV.md)
- **Main Tests**: [tests/README.md](tests/README.md)
- **Makefile Commands**: Run `make help`
- **GitHub Issues**: [Report Issue](https://github.com/brettleehari/aws-BTC-Agent/issues)

---

**Remember**: Tests are not just about catching bugs—they're about ensuring the codebase stays aligned with the architecture! 🎯
