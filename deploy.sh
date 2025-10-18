#!/bin/bash
# Deployment script for Market Hunter Agent

set -e

echo "=================================="
echo "Market Hunter Agent Deployment"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi
echo "✅ Python 3 found"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is required but not installed"
    exit 1
fi
echo "✅ AWS CLI found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi
echo "✅ AWS credentials configured"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Get configuration
echo ""
echo "=================================="
echo "Configuration"
echo "=================================="
read -p "Enter AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-east-1}

read -p "Enter Bedrock Agent ID (or 'skip' to create later): " AGENT_ID
read -p "Enter Bedrock Agent Alias ID (or 'skip' to create later): " ALIAS_ID

# Save configuration
cat > .env << EOF
AWS_REGION=$AWS_REGION
BEDROCK_AGENT_ID=$AGENT_ID
BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID
EOF

echo "✅ Configuration saved to .env"

# Optional database setup
echo ""
read -p "Set up PostgreSQL database? (y/n): " SETUP_DB
if [ "$SETUP_DB" = "y" ]; then
    read -p "Enter database connection string: " DB_URL
    echo "DATABASE_URL=$DB_URL" >> .env
    
    echo "Initializing database..."
    python3 << EOF
from src.database import MarketHunterDatabase
db = MarketHunterDatabase("$DB_URL")
db.create_tables()
print("✅ Database tables created")
EOF
fi

echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo ""

if [ "$AGENT_ID" = "skip" ]; then
    echo "1. Create Bedrock Agent:"
    echo "   python src/bedrock_agent_setup.py"
    echo ""
fi

echo "2. Update .env file with your Bedrock Agent details"
echo ""
echo "3. Test the agent:"
echo "   python src/example_usage.py"
echo ""
echo "4. Run in production:"
echo "   python src/production_service.py"
echo ""
echo "For detailed instructions, see README.md"
