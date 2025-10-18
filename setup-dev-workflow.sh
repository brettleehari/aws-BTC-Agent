#!/bin/bash
# Setup Development Workflow for Market Hunter Agent
# Installs pre-commit hooks, dependencies, and configures git

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Market Hunter Agent - Development Workflow Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in correct directory
if [ ! -f "README.md" ] || [ ! -d "src" ]; then
    echo "❌ Error: Please run this script from the repository root"
    exit 1
fi

echo -e "${BLUE}📋 Step 1: Checking prerequisites...${NC}"
echo ""

# Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✓ Python 3 found: $PYTHON_VERSION"
else
    echo "❌ Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check pip
if command -v pip3 >/dev/null 2>&1; then
    echo "✓ pip3 found"
else
    echo "❌ pip3 not found. Please install pip"
    exit 1
fi

# Check git
if command -v git >/dev/null 2>&1; then
    echo "✓ git found"
else
    echo "❌ git not found. Please install git"
    exit 1
fi

echo ""
echo -e "${BLUE}📦 Step 2: Installing Python dependencies...${NC}"
echo ""

# Upgrade pip
python3 -m pip install --upgrade pip

# Install main dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing requirements.txt..."
    pip install -r requirements.txt
    echo "✓ Main dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

# Create and install dev dependencies
echo ""
echo "Installing development dependencies..."

# Create dev requirements if missing
if [ ! -f "requirements-dev.txt" ]; then
    echo "Creating requirements-dev.txt..."
    cat > requirements-dev.txt <<EOF
# Development dependencies
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-xdist>=3.0.0
pytest-watch>=4.2.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0
bandit>=1.7.0
pre-commit>=3.0.0
coverage>=7.0.0
EOF
    echo "✓ requirements-dev.txt created"
fi

pip install -r requirements-dev.txt
echo "✓ Development dependencies installed"

echo ""
echo -e "${BLUE}🔧 Step 3: Setting up git hooks...${NC}"
echo ""

# Make pre-commit hook executable
if [ -f ".git/hooks/pre-commit" ]; then
    chmod +x .git/hooks/pre-commit
    echo "✓ Pre-commit hook made executable"
fi

# Install pre-commit framework
if command -v pre-commit >/dev/null 2>&1; then
    if [ -f ".pre-commit-config.yaml" ]; then
        echo "Installing pre-commit hooks..."
        pre-commit install
        echo "✓ Pre-commit framework installed"
    else
        echo "⚠️  .pre-commit-config.yaml not found, skipping"
    fi
else
    echo "⚠️  pre-commit command not available"
fi

echo ""
echo -e "${BLUE}🧪 Step 4: Running initial tests...${NC}"
echo ""

# Run goal alignment tests
echo "Running goal alignment tests..."
if python tests/test_goal_alignment.py; then
    echo -e "${GREEN}✓ Goal alignment tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Some goal alignment tests failed - this is normal for initial setup${NC}"
fi

echo ""
echo -e "${BLUE}⚙️  Step 5: Git configuration...${NC}"
echo ""

# Configure git to show better diffs
git config diff.python.xfuncname "^[ \t]*\\(class\\|def\\) .*" 2>/dev/null || true
echo "✓ Git diff configured for Python"

# Set up .gitignore if missing
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore..."
    cat > .gitignore <<EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local
*.log

# OS
.DS_Store
Thumbs.db

# AWS
.aws/
*.pem

# Jupyter
.ipynb_checkpoints/
EOF
    echo "✓ .gitignore created"
fi

echo ""
echo -e "${BLUE}📚 Step 6: Creating helpful aliases...${NC}"
echo ""

# Create shell alias suggestions
cat > .dev-aliases <<EOF
# Development aliases for Market Hunter Agent
# Add these to your ~/.bashrc or ~/.zshrc

# Testing
alias test-goals="python tests/test_goal_alignment.py"
alias test-unit="python tests/run_tests.py --unit"
alias test-all="python tests/run_tests.py --all"
alias test-fast="make test-fast"

# Code quality
alias fmt="make format"
alias lint="make lint"
alias check="make check"

# Agent operations
alias agent-run="python src/market_hunter_agent.py"
alias agent-test="python src/market_hunter_agent.py --test"
alias cost-report="python src/llm_router.py --cost-report"

# Git workflow
alias precommit="make pre-commit"
alias status="make status"
EOF

echo "✓ Development aliases created in .dev-aliases"
echo "  To use them: source .dev-aliases"

echo ""
echo -e "${BLUE}🎯 Step 7: Creating quick reference guide...${NC}"
echo ""

cat > QUICKSTART_DEV.md <<EOF
# Developer Quick Start

## 🚀 Quick Commands

\`\`\`bash
# Run goal alignment tests (most important!)
make test-goals
python tests/test_goal_alignment.py

# Run all tests
make test

# Run fast tests before commit
make test-fast

# Check code quality
make lint
make format
make check

# Git workflow
git add .
# Pre-commit hooks run automatically!
git commit -m "Your message"
git push
\`\`\`

## 📋 Before Each Commit

1. **Format code**: \`make format\`
2. **Run tests**: \`make test-goals\`
3. **Check quality**: \`make lint\`
4. **Commit**: Git hooks run automatically

## 🧪 Test Types

- **Goal Alignment** ⭐: Ensures codebase aligns with project goals
- **Unit Tests**: Fast tests without AWS
- **Integration Tests**: Tests with real AWS services
- **Evaluation Tests**: Agent performance evaluation

## 🔧 Development Workflow

\`\`\`bash
# 1. Make changes
vim src/market_hunter_agent.py

# 2. Format
make format

# 3. Test changes
make test-goals
make test-fast

# 4. Check quality
make lint

# 5. Commit (hooks run automatically)
git add .
git commit -m "feat: add new feature"

# 6. Push (CI/CD runs on GitHub)
git push
\`\`\`

## 🎯 Goal Alignment Criteria

The codebase is tested against 10 key goals:

1. ✓ **Autonomous decision-making** - No hardcoded rules
2. ✓ **Cost optimization** - Dynamic LLM routing
3. ✓ **Learning and adaptation** - Learns from experience
4. ✓ **Real-time performance** - Fast execution (<60s)
5. ✓ **Signal quality** - High-quality actionable signals
6. ✓ **Data source diversity** - 8+ different sources
7. ✓ **Clean architecture** - Separation of concerns
8. ✓ **Comprehensive testing** - Unit + integration + eval
9. ✓ **Documentation** - Well-documented code
10. ✓ **Production readiness** - Deployment automation

## 🚨 Common Issues

**Pre-commit hook failing?**
\`\`\`bash
# Run manually to see details
.git/hooks/pre-commit

# Or skip (not recommended)
git commit --no-verify
\`\`\`

**Tests failing?**
\`\`\`bash
# Run specific test
python tests/test_goal_alignment.py

# See details
pytest tests/test_agent_core.py -v
\`\`\`

**Import errors?**
\`\`\`bash
# Ensure dependencies installed
pip install -r requirements.txt
pip install -r requirements-dev.txt
\`\`\`

## 📊 Makefile Commands

Run \`make help\` to see all available commands!

## 🔗 Resources

- Full docs: [docs/](docs/)
- Test guide: [tests/README.md](tests/README.md)
- Deployment: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- LLM Router: [docs/LLM_ROUTER.md](docs/LLM_ROUTER.md)
EOF

echo "✓ Quick start guide created: QUICKSTART_DEV.md"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Development workflow setup complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Review quick start guide:"
echo "   ${BLUE}cat QUICKSTART_DEV.md${NC}"
echo ""
echo "2. Load development aliases:"
echo "   ${BLUE}source .dev-aliases${NC}"
echo ""
echo "3. Run goal alignment tests:"
echo "   ${BLUE}make test-goals${NC}"
echo ""
echo "4. See all available commands:"
echo "   ${BLUE}make help${NC}"
echo ""
echo "5. Start coding! Pre-commit hooks will run automatically."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Happy coding!"
