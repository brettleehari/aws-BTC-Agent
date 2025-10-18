# 🚀 Deployment Guide - AWS BTC Market Hunter Agent from GitHub

Complete guide to deploy the Market Hunter Agent to AWS directly from your GitHub repository.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Manual Deployment](#manual-deployment)
5. [Post-Deployment](#post-deployment)
6. [Troubleshooting](#troubleshooting)
7. [CI/CD with GitHub Actions](#cicd-with-github-actions)

---

## ✅ Prerequisites

### 1. AWS Account & CLI

```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output format (json)

# Verify credentials
aws sts get-caller-identity
```

### 2. Required IAM Permissions

Your AWS user/role needs:
- ✅ **Bedrock**: Full access to create agents
- ✅ **Lambda**: Create and update functions
- ✅ **IAM**: Create roles and attach policies
- ✅ **RDS**: Create PostgreSQL databases
- ✅ **S3**: Create buckets and upload objects
- ✅ **EventBridge**: Create rules and targets
- ✅ **CloudWatch**: View logs

### 3. Tools

```bash
# Python 3.9+
python3 --version

# Git
git --version

# AWS CLI
aws --version
```

### 4. GitHub Access

- Repository: `https://github.com/brettleehari/aws-BTC-Agent`
- For private repos: Generate GitHub Personal Access Token

---

## 🚀 Quick Start

### Automated Deployment (Recommended)

```bash
# 1. Download deployment script
curl -O https://raw.githubusercontent.com/brettleehari/aws-BTC-Agent/main/deploy-from-github.sh
chmod +x deploy-from-github.sh

# 2. Set environment variables (optional)
export AWS_REGION="us-east-1"
export ENVIRONMENT="production"
export DB_PASSWORD="your-secure-password"  # Optional: auto-generated if not set

# 3. Run deployment
./deploy-from-github.sh

# 4. Wait 10-15 minutes for deployment to complete
```

That's it! The script will:
- ✅ Clone repository
- ✅ Create S3 bucket
- ✅ Package Lambda functions
- ✅ Create IAM roles
- ✅ Deploy Lambda functions
- ✅ Create RDS database
- ✅ Create Bedrock Agent
- ✅ Set up EventBridge schedule
- ✅ Save configuration to `.env`

---

## 📖 Step-by-Step Deployment

### Step 1: Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/brettleehari/aws-BTC-Agent.git
cd aws-BTC-Agent

# Or for private repo with token
git clone https://YOUR_TOKEN@github.com/brettleehari/aws-BTC-Agent.git
cd aws-BTC-Agent
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import boto3; print('boto3:', boto3.__version__)"
```

### Step 3: Create S3 Bucket for Deployment

```bash
# Set variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export BUCKET_NAME="market-hunter-deployment-${AWS_ACCOUNT_ID}"
export AWS_REGION="us-east-1"

# Create bucket
aws s3 mb "s3://${BUCKET_NAME}" --region $AWS_REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket "${BUCKET_NAME}" \
  --versioning-configuration Status=Enabled
```

### Step 4: Package Lambda Functions

```bash
# Create package directory
mkdir -p lambda-packages

# Package each Lambda function
for dir in lambda_functions/*/; do
  lambda_name=$(basename "$dir")
  echo "Packaging $lambda_name..."
  cd "$dir"
  zip -r "../../lambda-packages/${lambda_name}.zip" .
  cd - > /dev/null
  
  # Upload to S3
  aws s3 cp "lambda-packages/${lambda_name}.zip" \
    "s3://${BUCKET_NAME}/lambda/${lambda_name}.zip"
done
```

### Step 5: Create IAM Roles

```bash
# Create Bedrock Agent Role
cat > bedrock-agent-trust-policy.json <<EOF
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

aws iam create-role \
  --role-name market-hunter-agent-role \
  --assume-role-policy-document file://bedrock-agent-trust-policy.json

aws iam attach-role-policy \
  --role-name market-hunter-agent-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Create Lambda Role
cat > lambda-trust-policy.json <<EOF
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

aws iam create-role \
  --role-name market-hunter-lambda-role \
  --assume-role-policy-document file://lambda-trust-policy.json

aws iam attach-role-policy \
  --role-name market-hunter-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name market-hunter-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# Wait for roles to propagate
sleep 10
```

### Step 6: Deploy Lambda Functions

```bash
export LAMBDA_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/market-hunter-lambda-role"

# Deploy each Lambda function
for package in lambda-packages/*.zip; do
  lambda_name=$(basename "$package" .zip)
  function_name="market-hunter-${lambda_name}"
  
  echo "Deploying $function_name..."
  
  aws lambda create-function \
    --function-name "$function_name" \
    --runtime python3.9 \
    --role "$LAMBDA_ROLE_ARN" \
    --handler lambda_function.lambda_handler \
    --code S3Bucket="${BUCKET_NAME}",S3Key="lambda/${lambda_name}.zip" \
    --timeout 30 \
    --memory-size 256
done
```

### Step 7: Create RDS Database

```bash
# Create PostgreSQL database
aws rds create-db-instance \
  --db-instance-identifier market-hunter-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username admin \
  --master-user-password "YOUR_SECURE_PASSWORD" \
  --allocated-storage 20 \
  --storage-type gp2 \
  --db-name market_hunter \
  --publicly-accessible \
  --backup-retention-period 7

# Wait for database to be available (5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier market-hunter-db

# Get database endpoint
DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier market-hunter-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

echo "Database endpoint: $DB_HOST"
```

### Step 8: Create Bedrock Agent

```bash
export AGENT_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/market-hunter-agent-role"

# Create agent
AGENT_ID=$(aws bedrock-agent create-agent \
  --agent-name market-hunter-agent \
  --agent-resource-role-arn "$AGENT_ROLE_ARN" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "You are an autonomous Bitcoin market intelligence agent that analyzes market data and generates trading signals." \
  --query 'agent.agentId' \
  --output text)

echo "Agent ID: $AGENT_ID"

# Prepare agent
aws bedrock-agent prepare-agent --agent-id "$AGENT_ID"

# Create alias
ALIAS_ID=$(aws bedrock-agent create-agent-alias \
  --agent-id "$AGENT_ID" \
  --agent-alias-name production \
  --query 'agentAlias.agentAliasId' \
  --output text)

echo "Alias ID: $ALIAS_ID"
```

### Step 9: Initialize Database Schema

```bash
# Create .env file
cat > .env <<EOF
BEDROCK_AGENT_ID=$AGENT_ID
BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID
DB_HOST=$DB_HOST
DB_NAME=market_hunter
DB_USER=admin
DB_PASSWORD=YOUR_SECURE_PASSWORD
AWS_REGION=$AWS_REGION
EOF

# Run database setup
python3 src/database.py --init
```

### Step 10: Deploy Agent Service

```bash
# Package agent service
zip -r agent-service.zip src/ config/

# Upload to S3
aws s3 cp agent-service.zip "s3://${BUCKET_NAME}/agent-service.zip"

# Load environment variables
source .env

# Create Lambda function
aws lambda create-function \
  --function-name market-hunter-service \
  --runtime python3.9 \
  --role "$LAMBDA_ROLE_ARN" \
  --handler production_service.handler \
  --code S3Bucket="${BUCKET_NAME}",S3Key="agent-service.zip" \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={BEDROCK_AGENT_ID=${BEDROCK_AGENT_ID},BEDROCK_AGENT_ALIAS_ID=${BEDROCK_AGENT_ALIAS_ID},DB_HOST=${DB_HOST},DB_NAME=${DB_NAME},DB_USER=${DB_USER},DB_PASSWORD=${DB_PASSWORD}}"
```

### Step 11: Create EventBridge Schedule

```bash
# Create rule (every 10 minutes)
aws events put-rule \
  --name market-hunter-schedule \
  --schedule-expression "rate(10 minutes)" \
  --state ENABLED

# Add Lambda permission
aws lambda add-permission \
  --function-name market-hunter-service \
  --statement-id market-hunter-schedule-invoke \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn "arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/market-hunter-schedule"

# Add target
FUNCTION_ARN="arn:aws:lambda:${AWS_REGION}:${AWS_ACCOUNT_ID}:function:market-hunter-service"

aws events put-targets \
  --rule market-hunter-schedule \
  --targets "Id=1,Arn=${FUNCTION_ARN}"
```

---

## 🛠️ Manual Deployment (AWS Console)

### 1. Create Bedrock Agent

1. Go to **Amazon Bedrock Console**
2. Navigate to **Agents** → **Create Agent**
3. Configure:
   - Name: `market-hunter-agent`
   - Model: `Claude 3 Sonnet`
   - Instructions: (copy from `config/agent_config.json`)
4. Create **Action Groups** for each Lambda function
5. **Prepare** and **Create Alias**

### 2. Create Lambda Functions

1. Go to **Lambda Console**
2. **Create Function** for each action group:
   - `query-whale-movements`
   - `query-derivatives-signals`
   - etc.
3. Upload code from `lambda_functions/` folders
4. Set timeout: 30 seconds
5. Set memory: 256 MB

### 3. Create RDS Database

1. Go to **RDS Console**
2. **Create Database** → PostgreSQL 15
3. Instance: `db.t3.micro`
4. Storage: 20 GB
5. Enable backups

### 4. Connect Everything

1. Update Lambda functions with DB credentials
2. Add Lambda permissions to Bedrock Agent
3. Create EventBridge rule for scheduling

---

## 📊 Post-Deployment

### Verify Deployment

```bash
# Test Bedrock Agent
aws bedrock-agent-runtime invoke-agent \
  --agent-id "$BEDROCK_AGENT_ID" \
  --agent-alias-id "$BEDROCK_AGENT_ALIAS_ID" \
  --session-id "test-session" \
  --input-text "Query whale movements" \
  --output-file response.txt

cat response.txt

# Check Lambda function
aws lambda invoke \
  --function-name market-hunter-service \
  --payload '{}' \
  response.json

cat response.json

# Check database
psql -h $DB_HOST -U admin -d market_hunter -c "SELECT * FROM agent_executions LIMIT 5;"
```

### Monitor Execution

```bash
# View CloudWatch Logs
aws logs tail /aws/lambda/market-hunter-service --follow

# Check agent metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationCount \
  --dimensions Name=AgentId,Value=$BEDROCK_AGENT_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Update Agent

```bash
# Update code
git pull

# Rebuild Lambda packages
./deploy-from-github.sh  # Runs full update

# Or update specific function
zip -r lambda-packages/query_whale_movements.zip lambda_functions/query_whale_movements/
aws s3 cp lambda-packages/query_whale_movements.zip "s3://${BUCKET_NAME}/lambda/query_whale_movements.zip"

aws lambda update-function-code \
  --function-name market-hunter-query_whale_movements \
  --s3-bucket "${BUCKET_NAME}" \
  --s3-key "lambda/query_whale_movements.zip"
```

---

## 🐛 Troubleshooting

### Issue: "AccessDeniedException"

**Solution**: Check IAM permissions
```bash
aws sts get-caller-identity
aws iam get-user-policy --user-name YOUR_USER --policy-name YOUR_POLICY
```

### Issue: "Role not found"

**Solution**: Wait for IAM propagation
```bash
sleep 10
aws iam get-role --role-name market-hunter-agent-role
```

### Issue: "Database connection failed"

**Solution**: Check security groups
```bash
# Get database security group
SG_ID=$(aws rds describe-db-instances \
  --db-instance-identifier market-hunter-db \
  --query 'DBInstances[0].VpcSecurityGroups[0].VpcSecurityGroupId' \
  --output text)

# Allow inbound from Lambda VPC
aws ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --protocol tcp \
  --port 5432 \
  --source-group LAMBDA_SG_ID
```

### Issue: "Lambda timeout"

**Solution**: Increase timeout
```bash
aws lambda update-function-configuration \
  --function-name market-hunter-service \
  --timeout 300
```

### Issue: "Bedrock model not available"

**Solution**: Request model access
```bash
# Go to Bedrock Console → Model access
# Request access to Claude 3 Sonnet
```

---

## 🔄 CI/CD with GitHub Actions

### Create GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run deployment script
        env:
          AWS_REGION: us-east-1
          ENVIRONMENT: production
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
        run: |
          chmod +x deploy-from-github.sh
          ./deploy-from-github.sh
      
      - name: Run tests
        run: |
          python tests/run_tests.py --unit
```

### Set GitHub Secrets

1. Go to **Repository Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `DB_PASSWORD`

### Deploy on Push

```bash
git add .
git commit -m "Update agent logic"
git push origin main

# GitHub Actions will automatically deploy
```

---

## 📋 Deployment Checklist

- [ ] AWS CLI installed and configured
- [ ] IAM permissions verified
- [ ] GitHub repository cloned
- [ ] Dependencies installed
- [ ] S3 bucket created
- [ ] Lambda functions packaged
- [ ] IAM roles created
- [ ] Lambda functions deployed
- [ ] RDS database created
- [ ] Bedrock Agent created
- [ ] Database schema initialized
- [ ] Agent service deployed
- [ ] EventBridge schedule created
- [ ] Deployment verified
- [ ] CloudWatch Logs checked
- [ ] Database connection tested
- [ ] GitHub Actions configured (optional)

---

## 💰 Cost Estimate

**Monthly costs** (approximate):

| Service | Usage | Cost |
|---------|-------|------|
| Bedrock Agent | 144 invocations/day | $10-20 |
| Bedrock Models (Claude 3) | Variable tokens | $20-50 |
| Lambda | 144 executions/day | $1-2 |
| RDS (t3.micro) | 730 hours/month | $15 |
| S3 | <1 GB | <$1 |
| **Total** | | **$47-88/month** |

With LLM Router optimization: **$30-50/month**

---

## 📞 Support

- **Documentation**: [README.md](README.md)
- **Test Guide**: [tests/README.md](tests/README.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **GitHub Issues**: [Report Issue](https://github.com/brettleehari/aws-BTC-Agent/issues)

---

## 🎉 Summary

You can deploy the Market Hunter Agent to AWS in 3 ways:

1. **Automated Script** (Recommended): `./deploy-from-github.sh`
2. **Step-by-Step CLI**: Follow commands above
3. **AWS Console**: Manual deployment via UI

The agent will run automatically every 10 minutes, querying market data and generating signals!

**Next steps**: Configure API keys for data sources and start monitoring! 🚀
