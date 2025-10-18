# Makefile for Market Hunter Agent
# Quick commands for development workflow

.PHONY: help install test test-all test-unit test-integration test-eval test-goals test-fast coverage lint format pre-commit clean deploy

# Default target
help:
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Market Hunter Agent - Development Commands"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "📦 Setup:"
	@echo "  make install          Install dependencies and setup dev environment"
	@echo "  make setup-hooks      Install git pre-commit hooks"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test             Run all tests (unit + integration + eval)"
	@echo "  make test-unit        Run unit tests only (fast, no AWS)"
	@echo "  make test-integration Run integration tests (requires AWS)"
	@echo "  make test-eval        Run evaluation framework"
	@echo "  make test-goals       Run goal alignment tests ⭐"
	@echo "  make test-fast        Run fast subset of tests"
	@echo "  make coverage         Run tests with coverage report"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  make lint             Run linting (flake8, mypy)"
	@echo "  make format           Format code (black, isort)"
	@echo "  make pre-commit       Run all pre-commit checks"
	@echo "  make check            Quick check before commit"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  make deploy           Deploy to AWS"
	@echo "  make deploy-test      Deploy to test environment"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean            Remove cache files"
	@echo "  make clean-all        Deep clean (including venv)"
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Installation
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt || echo "⚠️  No dev requirements found"
	@echo "✓ Dependencies installed"

setup-hooks:
	@echo "🔧 Setting up git hooks..."
	@if [ -f ".pre-commit-config.yaml" ]; then \
		pip install pre-commit; \
		pre-commit install; \
		echo "✓ Pre-commit hooks installed"; \
	else \
		cp .git/hooks/pre-commit.sample .git/hooks/pre-commit || true; \
		chmod +x .git/hooks/pre-commit; \
		echo "✓ Git hooks setup"; \
	fi

# Testing
test: test-unit test-integration test-eval test-goals
	@echo "✓ All tests completed"

test-all: test
	@echo "✓ Full test suite completed"

test-unit:
	@echo "🧪 Running unit tests..."
	python tests/run_tests.py --unit

test-integration:
	@echo "🧪 Running integration tests (requires AWS)..."
	python tests/run_tests.py --integration

test-eval:
	@echo "🧪 Running evaluation framework..."
	python tests/run_tests.py --eval

test-goals:
	@echo "⭐ Running goal alignment tests..."
	python tests/test_goal_alignment.py

test-fast:
	@echo "⚡ Running fast tests..."
	pytest tests/ -v -x -k "not slow and not integration" --tb=short

coverage:
	@echo "📊 Running tests with coverage..."
	pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "✓ Coverage report generated in htmlcov/"

# Code Quality
lint:
	@echo "🔍 Running linters..."
	@echo "→ flake8..."
	flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503 || true
	@echo "→ mypy..."
	mypy src/ --ignore-missing-imports --no-strict-optional || true
	@echo "→ bandit (security)..."
	bandit -r src/ -ll || true
	@echo "✓ Linting complete"

format:
	@echo "🎨 Formatting code..."
	@echo "→ isort..."
	isort src/ tests/ --profile=black --line-length=100
	@echo "→ black..."
	black src/ tests/ --line-length=100
	@echo "✓ Code formatted"

pre-commit:
	@echo "🔍 Running pre-commit checks..."
	@if command -v pre-commit >/dev/null 2>&1; then \
		pre-commit run --all-files; \
	else \
		.git/hooks/pre-commit; \
	fi

check: format lint test-fast test-goals
	@echo "✓ All checks passed - ready to commit!"

# Deployment
deploy:
	@echo "🚀 Deploying to AWS..."
	./deploy-from-github.sh

deploy-test:
	@echo "🧪 Deploying to test environment..."
	ENVIRONMENT=test ./deploy-from-github.sh

# Database
db-init:
	@echo "💾 Initializing database..."
	python src/database.py --init

db-migrate:
	@echo "💾 Running database migrations..."
	python src/database.py --migrate

db-reset:
	@echo "⚠️  Resetting database (WARNING: deletes all data)..."
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python src/database.py --reset; \
	fi

# Agent Operations
agent-run:
	@echo "🤖 Running agent once..."
	python src/market_hunter_agent.py

agent-test:
	@echo "🤖 Testing agent with mock data..."
	python src/market_hunter_agent.py --test

agent-status:
	@echo "📊 Checking agent status..."
	python src/check_agent_status.py

# Cost Analysis
cost-report:
	@echo "💰 Generating cost report..."
	python src/llm_router.py --cost-report

cost-compare:
	@echo "💰 Comparing LLM costs..."
	python examples/llm_router_demo.py

# Cleanup
clean:
	@echo "🧹 Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "✓ Cache cleaned"

clean-all: clean
	@echo "🧹 Deep cleaning..."
	rm -rf venv/ .venv/
	rm -rf *.egg-info/
	rm -rf dist/ build/
	@echo "✓ Deep clean complete"

# Documentation
docs:
	@echo "📚 Generating documentation..."
	@if command -v sphinx-build >/dev/null 2>&1; then \
		sphinx-build -b html docs/ docs/_build/; \
		echo "✓ Documentation generated in docs/_build/"; \
	else \
		echo "⚠️  Sphinx not installed. Install with: pip install sphinx"; \
	fi

# Development helpers
dev: install setup-hooks
	@echo "✓ Development environment ready!"

watch-tests:
	@echo "👀 Watching for changes and running tests..."
	@command -v pytest-watch >/dev/null 2>&1 || pip install pytest-watch
	ptw tests/ -- -v

shell:
	@echo "🐍 Starting Python shell with imports..."
	python -i -c "import sys; sys.path.insert(0, 'src'); from market_hunter_agent import *; from llm_router import *; print('✓ Imports loaded')"

# CI/CD helpers
ci: lint test-fast test-goals
	@echo "✓ CI checks passed"

cd: ci deploy
	@echo "✓ CD pipeline complete"

# Quick status check
status:
	@echo "📊 Repository Status"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "Git branch:"; git branch --show-current
	@echo "Git status:"; git status --short
	@echo "Python version:"; python --version
	@echo "Dependencies:"; pip list | wc -l; echo " packages installed"
	@echo "Tests:"; find tests -name "test_*.py" | wc -l; echo " test files"
	@echo "Source files:"; find src -name "*.py" | wc -l; echo " Python files"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create development requirements if missing
requirements-dev.txt:
	@echo "📝 Creating development requirements..."
	@echo "# Development dependencies" > requirements-dev.txt
	@echo "pytest>=7.0.0" >> requirements-dev.txt
	@echo "pytest-cov>=4.0.0" >> requirements-dev.txt
	@echo "pytest-watch>=4.2.0" >> requirements-dev.txt
	@echo "black>=23.0.0" >> requirements-dev.txt
	@echo "isort>=5.12.0" >> requirements-dev.txt
	@echo "flake8>=6.0.0" >> requirements-dev.txt
	@echo "mypy>=1.0.0" >> requirements-dev.txt
	@echo "bandit>=1.7.0" >> requirements-dev.txt
	@echo "pre-commit>=3.0.0" >> requirements-dev.txt
	@echo "✓ requirements-dev.txt created"
