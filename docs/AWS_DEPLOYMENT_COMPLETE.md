# 🚀 Complete AWS Deployment Guide - BTC Market Hunter Agent

**Deploying the complete application to AWS with Bedrock Agent Core**

---

## 📋 Overview

This guide will help you deploy the entire BTC Market Hunter Agent to AWS, including:

1. ✅ **Amazon Bedrock Agent** - Core reasoning engine with autonomous decision-making
2. ✅ **AWS Lambda** - Action handlers for market analysis
3. ✅ **Amazon DynamoDB** - Memory system (decisions, patterns, state, signals)
4. ✅ **Amazon EventBridge** - Automated scheduling
5. ✅ **Amazon CloudWatch** - Logging and monitoring
6. ✅ **AWS Systems Manager** - Configuration management

---

## 🎯 Project Requirements Met

Per `docs/projectrequirement.md`:

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| **LLM from AWS Bedrock** | Amazon Bedrock with Claude 3.5 Sonnet | ✅ |
| **Bedrock AgentCore** | Uses Bedrock Agent with primitives | ✅ |
| **Reasoning LLMs** | Claude 3.5 Sonnet for autonomous decisions | ✅ |
| **Autonomous Capabilities** | Source selection, signal generation, risk assessment | ✅ |
| **External Integrations** | 8 data sources (APIs, web search) | ✅ |
| **Database Integration** | DynamoDB for memory system | ✅ |

---

## ✅ Prerequisites

### 1. AWS Account Setup

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
# Enter:
#   AWS Access Key ID: [YOUR_KEY]
#   AWS Secret Access Key: [YOUR_SECRET]
#   Default region: us-east-1  # or us-west-2
#   Default output format: json

# Verify
aws sts get-caller-identity
```

### 2. Required AWS Permissions

Your IAM user/role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:*",
        "lambda:*",
        "dynamodb:*",
        "events:*",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "logs:*",
        "ssm:PutParameter",
        "ssm:GetParameter",
        "s3:CreateBucket",
        "s3:PutObject"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Enable Bedrock Models

**IMPORTANT:** You must enable model access in Bedrock first!

```bash
# Go to AWS Console
# Navigate to: Amazon Bedrock → Model access
# Request access to:
#   - Anthropic Claude 3.5 Sonnet
#   - Anthropic Claude 3 Haiku (optional, for routing)

# Or via CLI (if available in your region)
aws bedrock --region us-east-1 list-foundation-models
```

### 4. Check Region Availability

Not all services are available in all regions. Recommended regions:
- ✅ **us-east-1** (N. Virginia) - Most services available
- ✅ **us-west-2** (Oregon) - Good alternative

```bash
# Check Bedrock availability
aws bedrock list-foundation-models --region us-east-1

# Set your region
export AWS_REGION=us-east-1
```

---

## 🚀 Deployment Steps

### Step 1: Prepare the Application

```bash
# 1. Clone the repository (or ensure you're in the project directory)
cd /workspaces/aws-BTC-Agent

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify all components exist
ls -la src/
# Should see:
#   - market_hunter_agent_integrated.py (Main agent)
#   - bedrock_action_handler.py (Lambda function)
#   - llm_router.py (LLM routing logic)
#   - memory/ (Memory system)
```

### Step 2: Deploy DynamoDB Tables

```bash
# Set AWS credentials (if not already done)
export AWS_REGION=us-east-1

# Create the 4 memory system tables
cd /workspaces/aws-BTC-Agent
python deployment/dynamodb_setup.py create

# Verify tables
python deployment/dynamodb_setup.py status

# Expected output:
# ✅ agent_decisions (ACTIVE, 3 GSIs)
# ✅ agent_memory_ltm (ACTIVE, 3 GSIs)
# ✅ agent_state (ACTIVE, 2 GSIs)
# ✅ agent_signals (ACTIVE, 3 GSIs)
```

### Step 3: Package Lambda Function

```bash
# Create deployment package
cd /workspaces/aws-BTC-Agent

# Create a deployment directory
mkdir -p lambda_deployment
cd lambda_deployment

# Copy Lambda handler
cp ../src/bedrock_action_handler.py lambda_function.py

# Copy dependencies
cp -r ../src/memory .
cp -r ../src/llm_router.py .
cp -r ../src/market_hunter_agent_integrated.py .

# Install dependencies into package
pip install -t . boto3 requests pydantic

# Create ZIP file
zip -r market-hunter-lambda.zip .

echo "✅ Lambda package created: market-hunter-lambda.zip"
```

### Step 4: Create IAM Roles

```bash
# 1. Create Lambda execution role
aws iam create-role \
  --role-name MarketHunterLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 2. Attach policies to Lambda role
aws iam attach-role-policy \
  --role-name MarketHunterLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
  --role-name MarketHunterLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name MarketHunterLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess

# 3. Create Bedrock Agent role
aws iam create-role \
  --role-name MarketHunterBedrockAgentRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "bedrock.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 4. Attach policy for Bedrock Agent to invoke Lambda
aws iam put-role-policy \
  --role-name MarketHunterBedrockAgentRole \
  --policy-name BedrockAgentInvokeLambda \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "lambda:InvokeFunction",
      "Resource": "*"
    }]
  }'

echo "✅ IAM roles created"
```

### Step 5: Deploy Lambda Function

```bash
# Get the Lambda role ARN
LAMBDA_ROLE_ARN=$(aws iam get-role --role-name MarketHunterLambdaRole --query 'Role.Arn' --output text)

# Create Lambda function
cd /workspaces/aws-BTC-Agent/lambda_deployment

aws lambda create-function \
  --function-name market-hunter-action-handler \
  --runtime python3.12 \
  --role $LAMBDA_ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://market-hunter-lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={
    AWS_REGION=$AWS_REGION,
    DECISIONS_TABLE=agent_decisions,
    MEMORY_TABLE=agent_memory_ltm,
    STATE_TABLE=agent_state,
    SIGNALS_TABLE=agent_signals
  }"

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name market-hunter-action-handler \
  --query 'Configuration.FunctionArn' \
  --output text)

echo "✅ Lambda function deployed"
echo "Lambda ARN: $LAMBDA_ARN"
```

### Step 6: Create Bedrock Agent

```bash
# Get Bedrock Agent role ARN
BEDROCK_ROLE_ARN=$(aws iam get-role --role-name MarketHunterBedrockAgentRole --query 'Role.Arn' --output text)

# Create the agent
aws bedrock-agent create-agent \
  --region $AWS_REGION \
  --agent-name "BTC-Market-Hunter" \
  --foundation-model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --instruction "You are an autonomous Bitcoin market analyst. Your role is to:
1. Assess current market conditions (volatility, trend, trading session)
2. Autonomously select the best data sources based on market context
3. Analyze signals from multiple sources
4. Generate market insights and risk assessments
5. Make data-driven decisions without human intervention

You have access to 8 market data sources and can autonomously choose which to query based on market conditions. You learn from past decisions and adapt your strategy." \
  --agent-resource-role-arn $BEDROCK_ROLE_ARN \
  --idle-session-ttl-in-seconds 1800

# Get Agent ID from output
AGENT_ID=$(aws bedrock-agent list-agents --region $AWS_REGION \
  --query "agentSummaries[?agentName=='BTC-Market-Hunter'].agentId" \
  --output text)

echo "✅ Bedrock Agent created"
echo "Agent ID: $AGENT_ID"
```

### Step 7: Create Action Group

```bash
# Create action group JSON schema
cat > action-group-schema.json << 'EOF'
{
  "openapi": "3.0.0",
  "info": {
    "title": "Market Hunter Actions",
    "version": "1.0.0"
  },
  "paths": {
    "/analyze-market": {
      "post": {
        "summary": "Analyze current market conditions",
        "operationId": "analyzeMarket",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "btc_price": {"type": "number"},
                  "change_24h": {"type": "number"},
                  "volume_ratio": {"type": "number"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Market analysis result"
          }
        }
      }
    },
    "/select-sources": {
      "post": {
        "summary": "Autonomously select data sources based on market context",
        "operationId": "selectSources",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "volatility": {"type": "string"},
                  "trend": {"type": "string"},
                  "session": {"type": "string"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Selected sources with reasoning"
          }
        }
      }
    },
    "/fetch-data": {
      "post": {
        "summary": "Fetch data from specified sources",
        "operationId": "fetchData",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "sources": {
                    "type": "array",
                    "items": {"type": "string"}
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Fetched market data"
          }
        }
      }
    },
    "/generate-signals": {
      "post": {
        "summary": "Generate trading signals from market data",
        "operationId": "generateSignals",
        "requestBody": {
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "properties": {
                  "market_data": {"type": "object"},
                  "context": {"type": "object"}
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Generated signals"
          }
        }
      }
    }
  }
}
EOF

# Upload schema to S3 (required for Bedrock Agent)
S3_BUCKET="market-hunter-agent-$(date +%s)"
aws s3 mb s3://$S3_BUCKET --region $AWS_REGION
aws s3 cp action-group-schema.json s3://$S3_BUCKET/

# Create action group
aws bedrock-agent create-agent-action-group \
  --region $AWS_REGION \
  --agent-id $AGENT_ID \
  --agent-version DRAFT \
  --action-group-name "MarketHunterActions" \
  --action-group-executor "{\"lambda\":\"$LAMBDA_ARN\"}" \
  --api-schema "{\"s3\":{\"s3BucketName\":\"$S3_BUCKET\",\"s3ObjectKey\":\"action-group-schema.json\"}}"

echo "✅ Action group created"
```

### Step 8: Prepare and Create Agent Alias

```bash
# Prepare the agent (required before creating alias)
aws bedrock-agent prepare-agent \
  --region $AWS_REGION \
  --agent-id $AGENT_ID

# Wait for preparation to complete (usually 1-2 minutes)
echo "Waiting for agent preparation..."
sleep 60

# Create agent alias
aws bedrock-agent create-agent-alias \
  --region $AWS_REGION \
  --agent-id $AGENT_ID \
  --agent-alias-name "production" \
  --description "Production alias for Market Hunter Agent"

# Get Alias ID
ALIAS_ID=$(aws bedrock-agent list-agent-aliases \
  --region $AWS_REGION \
  --agent-id $AGENT_ID \
  --query "agentAliasSummaries[?agentAliasName=='production'].agentAliasId" \
  --output text)

echo "✅ Agent alias created"
echo "Alias ID: $ALIAS_ID"
```

### Step 9: Add Lambda Permission for Bedrock

```bash
# Allow Bedrock Agent to invoke Lambda
aws lambda add-permission \
  --function-name market-hunter-action-handler \
  --statement-id bedrock-agent-invoke \
  --action lambda:InvokeFunction \
  --principal bedrock.amazonaws.com \
  --source-arn "arn:aws:bedrock:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):agent/$AGENT_ID"

echo "✅ Lambda permission added for Bedrock Agent"
```

### Step 10: Create EventBridge Schedule (Optional)

```bash
# Create EventBridge rule for hourly execution
aws events put-rule \
  --name market-hunter-hourly \
  --schedule-expression "rate(1 hour)" \
  --description "Trigger Market Hunter Agent every hour"

# Create IAM role for EventBridge
aws iam create-role \
  --role-name MarketHunterEventBridgeRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "events.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy to allow invoking Bedrock Agent
aws iam put-role-policy \
  --role-name MarketHunterEventBridgeRole \
  --policy-name InvokeBedrockAgent \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Action\": \"bedrock:InvokeAgent\",
      \"Resource\": \"arn:aws:bedrock:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):agent-alias/$AGENT_ID/*\"
    }]
  }"

# Create target for the rule (this would require a Lambda trigger or custom solution)
# For now, we'll invoke manually or via Lambda

echo "✅ EventBridge schedule created (manual invocation required)"
```

### Step 11: Save Configuration

```bash
# Create .env file with all deployment info
cat > .env << EOF
# AWS Configuration
AWS_REGION=$AWS_REGION
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Bedrock Agent
BEDROCK_AGENT_ID=$AGENT_ID
BEDROCK_AGENT_ALIAS_ID=$ALIAS_ID
BEDROCK_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0

# Lambda
LAMBDA_FUNCTION_NAME=market-hunter-action-handler
LAMBDA_ARN=$LAMBDA_ARN

# DynamoDB Tables
DECISIONS_TABLE=agent_decisions
MEMORY_TABLE=agent_memory_ltm
STATE_TABLE=agent_state
SIGNALS_TABLE=agent_signals

# S3
S3_BUCKET=$S3_BUCKET

# IAM Roles
LAMBDA_ROLE_ARN=$LAMBDA_ROLE_ARN
BEDROCK_ROLE_ARN=$BEDROCK_ROLE_ARN
EOF

echo "✅ Configuration saved to .env"
```

---

## 🧪 Test the Deployment

### Test 1: Invoke Bedrock Agent

```python
# test_agent_invocation.py
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Bedrock Agent Runtime client
client = boto3.client('bedrock-agent-runtime', region_name=os.getenv('AWS_REGION'))

# Invoke agent
response = client.invoke_agent(
    agentId=os.getenv('BEDROCK_AGENT_ID'),
    agentAliasId=os.getenv('BEDROCK_AGENT_ALIAS_ID'),
    sessionId='test-session-1',
    inputText='Analyze the current Bitcoin market conditions and recommend which data sources to query.'
)

# Print response
print("Agent Response:")
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        if 'bytes' in chunk:
            print(chunk['bytes'].decode('utf-8'), end='')
```

Run the test:
```bash
python test_agent_invocation.py
```

### Test 2: Check DynamoDB Tables

```bash
# Check if decisions are being logged
aws dynamodb scan \
  --table-name agent_decisions \
  --limit 5 \
  --region $AWS_REGION

# Check agent state
aws dynamodb scan \
  --table-name agent_state \
  --limit 5 \
  --region $AWS_REGION
```

### Test 3: Check Lambda Logs

```bash
# View Lambda logs
aws logs tail /aws/lambda/market-hunter-action-handler --follow
```

---

## 📊 Monitoring and Maintenance

### CloudWatch Dashboards

```bash
# View Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Invocations \
  --dimensions Name=FunctionName,Value=market-hunter-action-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Cost Monitoring

Expected monthly costs (for demo/testing):
- **DynamoDB**: ~$3.50 (On-Demand)
- **Lambda**: ~$1-5 (depends on invocations)
- **Bedrock**: ~$10-50 (depends on usage)
- **Total**: ~$15-60/month

---

## 🔧 Troubleshooting

### Common Issues

**1. Bedrock Agent not responding:**
```bash
# Check agent status
aws bedrock-agent get-agent --agent-id $AGENT_ID --region $AWS_REGION

# Re-prepare agent
aws bedrock-agent prepare-agent --agent-id $AGENT_ID --region $AWS_REGION
```

**2. Lambda timeout errors:**
```bash
# Increase timeout
aws lambda update-function-configuration \
  --function-name market-hunter-action-handler \
  --timeout 900
```

**3. DynamoDB permission errors:**
```bash
# Verify Lambda role has DynamoDB access
aws iam list-attached-role-policies --role-name MarketHunterLambdaRole
```

---

## 🎯 Next Steps

1. **Enable Real Data Sources**
   - Add API keys to Lambda environment variables
   - Configure external data source endpoints

2. **Set Up Monitoring**
   - Create CloudWatch dashboards
   - Set up alarms for errors

3. **Optimize Costs**
   - Use provisioned concurrency for Lambda if needed
   - Consider DynamoDB reserved capacity for production

4. **Production Hardening**
   - Add VPC configuration
   - Implement secrets management (AWS Secrets Manager)
   - Set up backup policies

---

## ✅ Deployment Checklist

- [ ] AWS CLI configured
- [ ] Bedrock model access enabled
- [ ] DynamoDB tables created
- [ ] Lambda function deployed
- [ ] IAM roles configured
- [ ] Bedrock Agent created
- [ ] Action group configured
- [ ] Agent alias created
- [ ] Lambda permissions set
- [ ] Configuration saved (.env)
- [ ] Agent tested successfully
- [ ] Monitoring configured

---

## 📚 Additional Resources

- [AWS Bedrock Agent Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html)
- [Project Documentation](./docs/)
- [Architecture Diagram](./docs/ARCHITECTURE.md)
- [Testing Guide](./docs/TESTING.md)

---

**🎉 Congratulations! Your BTC Market Hunter Agent is deployed to AWS!**

The agent is now running with:
- ✅ Amazon Bedrock for autonomous reasoning
- ✅ Lambda functions for action execution  
- ✅ DynamoDB for memory and state
- ✅ Full autonomous decision-making capabilities
