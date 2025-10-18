#!/bin/bash

###############################################################################
# AWS BTC Market Hunter Agent - Deployment Script
#
# This script deploys the Market Hunter Agent to AWS from GitHub
# 
# Prerequisites:
# - AWS CLI configured with appropriate credentials
# - GitHub repository access
# - Required IAM permissions for Bedrock, Lambda, RDS, etc.
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
GITHUB_REPO="${GITHUB_REPO:-brettleehari/aws-BTC-Agent}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
AGENT_NAME="market-hunter-agent"
STACK_NAME="${STACK_NAME:-market-hunter-stack}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    AWS BTC Market Hunter Agent - Deployment Script            ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "AWS CLI found"
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Run 'aws configure'"
        exit 1
    fi
    
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    print_success "AWS credentials valid (Account: $ACCOUNT_ID)"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install it first."
        exit 1
    fi
    print_success "Git found"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
    
    # Check required Python packages
    print_status "Checking Python packages..."
    python3 -c "import boto3" 2>/dev/null || {
        print_warning "boto3 not found. Will install dependencies later."
    }
    
    echo ""
}

# Function to clone repository
clone_repository() {
    print_status "Cloning repository from GitHub..."
    
    DEPLOY_DIR="/tmp/market-hunter-deploy-$(date +%s)"
    
    if [ -n "$GITHUB_TOKEN" ]; then
        git clone "https://${GITHUB_TOKEN}@github.com/${GITHUB_REPO}.git" "$DEPLOY_DIR"
    else
        git clone "https://github.com/${GITHUB_REPO}.git" "$DEPLOY_DIR"
    fi
    
    cd "$DEPLOY_DIR"
    print_success "Repository cloned to $DEPLOY_DIR"
    echo ""
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    python3 -m pip install -r requirements.txt --quiet
    
    print_success "Dependencies installed"
    echo ""
}

# Function to create S3 bucket for deployment artifacts
create_s3_bucket() {
    print_status "Creating S3 bucket for deployment artifacts..."
    
    BUCKET_NAME="${AGENT_NAME}-deployment-${ACCOUNT_ID}"
    
    # Check if bucket exists
    if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
        print_warning "Bucket already exists: ${BUCKET_NAME}"
    else
        if [ "$AWS_REGION" = "us-east-1" ]; then
            aws s3 mb "s3://${BUCKET_NAME}"
        else
            aws s3 mb "s3://${BUCKET_NAME}" --region "$AWS_REGION"
        fi
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "${BUCKET_NAME}" \
            --versioning-configuration Status=Enabled
        
        print_success "S3 bucket created: ${BUCKET_NAME}"
    fi
    
    echo ""
}

# Function to package Lambda functions
package_lambda_functions() {
    print_status "Packaging Lambda functions..."
    
    mkdir -p lambda-packages
    
    # Package each Lambda function
    for lambda_dir in lambda_functions/*/; do
        if [ -d "$lambda_dir" ]; then
            lambda_name=$(basename "$lambda_dir")
            print_status "Packaging $lambda_name..."
            
            cd "$lambda_dir"
            zip -r "../../lambda-packages/${lambda_name}.zip" . -q
            cd - > /dev/null
            
            # Upload to S3
            aws s3 cp "lambda-packages/${lambda_name}.zip" \
                "s3://${BUCKET_NAME}/lambda/${lambda_name}.zip"
        fi
    done
    
    print_success "Lambda functions packaged and uploaded"
    echo ""
}

# Function to create IAM roles
create_iam_roles() {
    print_status "Creating IAM roles..."
    
    # Bedrock Agent Role
    AGENT_ROLE_NAME="${AGENT_NAME}-role"
    
    cat > /tmp/bedrock-agent-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    # Create role if it doesn't exist
    if aws iam get-role --role-name "$AGENT_ROLE_NAME" 2>/dev/null; then
        print_warning "IAM role already exists: $AGENT_ROLE_NAME"
    else
        aws iam create-role \
            --role-name "$AGENT_ROLE_NAME" \
            --assume-role-policy-document file:///tmp/bedrock-agent-trust-policy.json \
            --description "Role for Market Hunter Bedrock Agent"
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name "$AGENT_ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        
        print_success "IAM role created: $AGENT_ROLE_NAME"
    fi
    
    # Lambda Execution Role
    LAMBDA_ROLE_NAME="${AGENT_NAME}-lambda-role"
    
    cat > /tmp/lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    if aws iam get-role --role-name "$LAMBDA_ROLE_NAME" 2>/dev/null; then
        print_warning "Lambda role already exists: $LAMBDA_ROLE_NAME"
    else
        aws iam create-role \
            --role-name "$LAMBDA_ROLE_NAME" \
            --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
            --description "Role for Market Hunter Lambda functions"
        
        # Attach policies
        aws iam attach-role-policy \
            --role-name "$LAMBDA_ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
        
        aws iam attach-role-policy \
            --role-name "$LAMBDA_ROLE_NAME" \
            --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        
        print_success "Lambda role created: $LAMBDA_ROLE_NAME"
    fi
    
    # Wait for roles to propagate
    print_status "Waiting for IAM roles to propagate..."
    sleep 10
    
    echo ""
}

# Function to deploy Lambda functions
deploy_lambda_functions() {
    print_status "Deploying Lambda functions..."
    
    LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${AGENT_NAME}-lambda-role"
    
    # Get list of Lambda packages
    for lambda_package in lambda-packages/*.zip; do
        lambda_name=$(basename "$lambda_package" .zip)
        function_name="${AGENT_NAME}-${lambda_name}"
        
        print_status "Deploying $function_name..."
        
        # Check if function exists
        if aws lambda get-function --function-name "$function_name" 2>/dev/null; then
            # Update existing function
            aws lambda update-function-code \
                --function-name "$function_name" \
                --s3-bucket "${BUCKET_NAME}" \
                --s3-key "lambda/${lambda_name}.zip" \
                > /dev/null
            
            print_success "Updated Lambda function: $function_name"
        else
            # Create new function
            aws lambda create-function \
                --function-name "$function_name" \
                --runtime python3.9 \
                --role "$LAMBDA_ROLE_ARN" \
                --handler lambda_function.lambda_handler \
                --code S3Bucket="${BUCKET_NAME}",S3Key="lambda/${lambda_name}.zip" \
                --timeout 30 \
                --memory-size 256 \
                > /dev/null
            
            print_success "Created Lambda function: $function_name"
        fi
    done
    
    echo ""
}

# Function to create RDS PostgreSQL database
create_database() {
    print_status "Creating RDS PostgreSQL database..."
    
    DB_INSTANCE_ID="${AGENT_NAME}-db"
    DB_NAME="market_hunter"
    DB_USERNAME="${DB_USERNAME:-admin}"
    DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 32 | tr -d /=+ | cut -c1-25)}"
    
    # Check if DB instance exists
    if aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" 2>/dev/null; then
        print_warning "Database already exists: $DB_INSTANCE_ID"
    else
        print_status "Creating database instance (this takes 5-10 minutes)..."
        
        aws rds create-db-instance \
            --db-instance-identifier "$DB_INSTANCE_ID" \
            --db-instance-class db.t3.micro \
            --engine postgres \
            --engine-version 15.3 \
            --master-username "$DB_USERNAME" \
            --master-user-password "$DB_PASSWORD" \
            --allocated-storage 20 \
            --storage-type gp2 \
            --db-name "$DB_NAME" \
            --publicly-accessible \
            --backup-retention-period 7 \
            > /dev/null
        
        # Wait for database to be available
        print_status "Waiting for database to be available..."
        aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_ID"
        
        print_success "Database created: $DB_INSTANCE_ID"
        
        # Save credentials
        echo "DB_HOST=$(aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --query 'DBInstances[0].Endpoint.Address' --output text)" > .env
        echo "DB_NAME=$DB_NAME" >> .env
        echo "DB_USERNAME=$DB_USERNAME" >> .env
        echo "DB_PASSWORD=$DB_PASSWORD" >> .env
        
        print_success "Database credentials saved to .env"
    fi
    
    echo ""
}

# Function to create Bedrock Agent
create_bedrock_agent() {
    print_status "Creating Bedrock Agent..."
    
    AGENT_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${AGENT_NAME}-role"
    
    # Check if agent exists
    EXISTING_AGENT=$(aws bedrock-agent list-agents --query "agentSummaries[?agentName=='${AGENT_NAME}'].agentId" --output text 2>/dev/null || echo "")
    
    if [ -n "$EXISTING_AGENT" ]; then
        print_warning "Bedrock Agent already exists: $EXISTING_AGENT"
        AGENT_ID="$EXISTING_AGENT"
    else
        # Create agent
        AGENT_ID=$(aws bedrock-agent create-agent \
            --agent-name "$AGENT_NAME" \
            --agent-resource-role-arn "$AGENT_ROLE_ARN" \
            --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
            --instruction "You are an autonomous Bitcoin market intelligence agent..." \
            --query 'agent.agentId' \
            --output text)
        
        print_success "Bedrock Agent created: $AGENT_ID"
    fi
    
    # Create action groups (Lambda functions)
    print_status "Creating action groups..."
    
    # TODO: Create action groups for each Lambda function
    # This would require creating OpenAPI schemas for each action group
    
    # Prepare agent
    print_status "Preparing agent..."
    aws bedrock-agent prepare-agent --agent-id "$AGENT_ID" > /dev/null
    
    # Create alias
    ALIAS_NAME="${ENVIRONMENT}"
    ALIAS_ID=$(aws bedrock-agent list-agent-aliases \
        --agent-id "$AGENT_ID" \
        --query "agentAliasSummaries[?agentAliasName=='${ALIAS_NAME}'].agentAliasId" \
        --output text 2>/dev/null || echo "")
    
    if [ -z "$ALIAS_ID" ]; then
        ALIAS_ID=$(aws bedrock-agent create-agent-alias \
            --agent-id "$AGENT_ID" \
            --agent-alias-name "$ALIAS_NAME" \
            --query 'agentAlias.agentAliasId' \
            --output text)
        
        print_success "Agent alias created: $ALIAS_ID"
    else
        print_warning "Agent alias already exists: $ALIAS_ID"
    fi
    
    # Save agent info
    echo "BEDROCK_AGENT_ID=$AGENT_ID" >> .env
    echo "BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID" >> .env
    
    echo ""
}

# Function to run database migrations
run_database_migrations() {
    print_status "Running database migrations..."
    
    # Load database credentials
    source .env
    
    # Run database setup script
    python3 src/database.py --init
    
    print_success "Database schema created"
    echo ""
}

# Function to deploy agent service
deploy_agent_service() {
    print_status "Deploying agent service..."
    
    # Create Lambda function for agent service
    zip -r agent-service.zip src/ config/ -q
    
    aws s3 cp agent-service.zip "s3://${BUCKET_NAME}/agent-service.zip"
    
    LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${AGENT_NAME}-lambda-role"
    SERVICE_FUNCTION_NAME="${AGENT_NAME}-service"
    
    # Load environment variables
    source .env
    
    ENV_VARS="Variables={BEDROCK_AGENT_ID=${BEDROCK_AGENT_ID},BEDROCK_AGENT_ALIAS_ID=${BEDROCK_AGENT_ALIAS_ID},DB_HOST=${DB_HOST},DB_NAME=${DB_NAME},DB_USER=${DB_USERNAME},DB_PASSWORD=${DB_PASSWORD}}"
    
    if aws lambda get-function --function-name "$SERVICE_FUNCTION_NAME" 2>/dev/null; then
        aws lambda update-function-code \
            --function-name "$SERVICE_FUNCTION_NAME" \
            --s3-bucket "${BUCKET_NAME}" \
            --s3-key "agent-service.zip" \
            > /dev/null
        
        aws lambda update-function-configuration \
            --function-name "$SERVICE_FUNCTION_NAME" \
            --environment "$ENV_VARS" \
            > /dev/null
        
        print_success "Updated agent service"
    else
        aws lambda create-function \
            --function-name "$SERVICE_FUNCTION_NAME" \
            --runtime python3.9 \
            --role "$LAMBDA_ROLE_ARN" \
            --handler production_service.handler \
            --code S3Bucket="${BUCKET_NAME}",S3Key="agent-service.zip" \
            --timeout 300 \
            --memory-size 512 \
            --environment "$ENV_VARS" \
            > /dev/null
        
        print_success "Created agent service"
    fi
    
    echo ""
}

# Function to create EventBridge rule for scheduled execution
create_schedule() {
    print_status "Creating EventBridge schedule..."
    
    RULE_NAME="${AGENT_NAME}-schedule"
    SERVICE_FUNCTION_NAME="${AGENT_NAME}-service"
    
    # Create rule (every 10 minutes)
    aws events put-rule \
        --name "$RULE_NAME" \
        --schedule-expression "rate(10 minutes)" \
        --state ENABLED \
        > /dev/null
    
    # Add Lambda permission
    aws lambda add-permission \
        --function-name "$SERVICE_FUNCTION_NAME" \
        --statement-id "${RULE_NAME}-invoke" \
        --action "lambda:InvokeFunction" \
        --principal events.amazonaws.com \
        --source-arn "arn:aws:events:${AWS_REGION}:${ACCOUNT_ID}:rule/${RULE_NAME}" \
        2>/dev/null || print_warning "Permission already exists"
    
    # Add target
    FUNCTION_ARN="arn:aws:lambda:${AWS_REGION}:${ACCOUNT_ID}:function:${SERVICE_FUNCTION_NAME}"
    
    aws events put-targets \
        --rule "$RULE_NAME" \
        --targets "Id=1,Arn=${FUNCTION_ARN}" \
        > /dev/null
    
    print_success "EventBridge schedule created (every 10 minutes)"
    echo ""
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              DEPLOYMENT COMPLETED SUCCESSFULLY                 ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    source .env 2>/dev/null || true
    
    echo -e "${BLUE}Deployment Information:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  AWS Region:              $AWS_REGION"
    echo "  AWS Account:             $ACCOUNT_ID"
    echo "  Environment:             $ENVIRONMENT"
    echo ""
    echo "  Bedrock Agent ID:        ${BEDROCK_AGENT_ID:-Not created}"
    echo "  Bedrock Agent Alias:     ${BEDROCK_AGENT_ALIAS_ID:-Not created}"
    echo ""
    echo "  Database Endpoint:       ${DB_HOST:-Not created}"
    echo "  Database Name:           ${DB_NAME:-Not created}"
    echo ""
    echo "  S3 Bucket:               ${BUCKET_NAME}"
    echo "  Service Function:        ${AGENT_NAME}-service"
    echo "  Schedule:                Every 10 minutes"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Configure data source APIs (exchange, blockchain explorers)"
    echo "  2. Update Lambda functions with real API integrations"
    echo "  3. Test agent: aws bedrock-agent-runtime invoke-agent ..."
    echo "  4. Monitor CloudWatch Logs for execution"
    echo "  5. Check database for stored signals and metrics"
    echo ""
    echo -e "${BLUE}Configuration saved to: .env${NC}"
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    clone_repository
    install_dependencies
    create_s3_bucket
    package_lambda_functions
    create_iam_roles
    deploy_lambda_functions
    create_database
    create_bedrock_agent
    run_database_migrations
    deploy_agent_service
    create_schedule
    display_summary
}

# Run main function
main
