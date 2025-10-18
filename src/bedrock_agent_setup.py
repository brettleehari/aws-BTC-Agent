"""
Bedrock Agent Configuration and Setup
Instructions for creating the Market Hunter Agent in Amazon Bedrock
"""

AGENT_CONFIGURATION = {
    "agent_name": "MarketHunterAgent",
    "description": "Autonomous Bitcoin market intelligence agent that independently selects and queries data sources based on market conditions",
    "foundation_model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "instruction": """
You are an autonomous market intelligence agent for Bitcoin trading. Your role is to analyze market data and provide actionable insights.

When querying data sources, you should:
1. Understand the current market context (volatility, trend, trading session)
2. Analyze the requested data source thoroughly
3. Extract actionable insights relevant to the market conditions
4. Identify potential trading signals or risk factors
5. Provide clear, concise analysis

Available data sources:
- whaleMovements: Large on-chain Bitcoin transactions (>100 BTC)
- narrativeShifts: Social media trends and sentiment shifts
- arbitrageOpportunities: Price differences across exchanges
- influencerSignals: Technical analysis and price predictions from known traders
- technicalBreakouts: Chart pattern analysis and breakout detection
- institutionalFlows: Large institutional holder movements
- derivativesSignals: Funding rates, open interest, liquidations
- macroSignals: Fear & Greed Index, market-wide sentiment

For each query:
1. Acknowledge the data source being queried
2. Provide relevant market data
3. Highlight any significant patterns or anomalies
4. Suggest potential implications for trading

When analyzing multiple sources:
1. Synthesize information across sources
2. Identify confluent signals
3. Assess signal strength and confidence
4. Recommend specific actions

Always consider:
- Signal reliability and confidence
- Market context and conditions
- Risk factors and uncertainties
- Timing and urgency of actions
""",
    "action_groups": [
        {
            "name": "MarketDataQueries",
            "description": "Query various Bitcoin market data sources",
            "functions": [
                {
                    "name": "query_whale_movements",
                    "description": "Query large on-chain Bitcoin transactions (>100 BTC)",
                    "parameters": {
                        "threshold_btc": {
                            "type": "number",
                            "description": "Minimum transaction size in BTC",
                            "required": False
                        },
                        "timeframe_hours": {
                            "type": "number",
                            "description": "Look back period in hours",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_narrative_shifts",
                    "description": "Query social media trends and sentiment shifts",
                    "parameters": {
                        "platforms": {
                            "type": "array",
                            "description": "Social platforms to analyze",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_arbitrage_opportunities",
                    "description": "Query price differences across exchanges",
                    "parameters": {
                        "min_spread_percent": {
                            "type": "number",
                            "description": "Minimum spread percentage",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_influencer_signals",
                    "description": "Query technical analysis from known traders",
                    "parameters": {
                        "min_followers": {
                            "type": "number",
                            "description": "Minimum follower count",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_technical_breakouts",
                    "description": "Query chart patterns and breakout detection",
                    "parameters": {
                        "timeframes": {
                            "type": "array",
                            "description": "Chart timeframes to analyze",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_institutional_flows",
                    "description": "Query large institutional holder movements",
                    "parameters": {
                        "min_holding_btc": {
                            "type": "number",
                            "description": "Minimum holding size",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_derivatives_signals",
                    "description": "Query funding rates, open interest, and liquidations",
                    "parameters": {
                        "exchanges": {
                            "type": "array",
                            "description": "Derivative exchanges to query",
                            "required": False
                        }
                    }
                },
                {
                    "name": "query_macro_signals",
                    "description": "Query Fear & Greed Index and market-wide sentiment",
                    "parameters": {}
                }
            ]
        }
    ],
    "knowledge_bases": [
        {
            "name": "Bitcoin Market Knowledge",
            "description": "Historical Bitcoin market data, patterns, and trading strategies",
            "data_sources": [
                "s3://your-bucket/bitcoin-market-data/",
                "s3://your-bucket/trading-patterns/",
                "s3://your-bucket/market-indicators/"
            ]
        }
    ]
}


# Lambda function template for action group implementation
LAMBDA_FUNCTION_TEMPLATE = """
import json
import boto3
import requests
from datetime import datetime, timedelta

def query_whale_movements(threshold_btc=100, timeframe_hours=24):
    '''Query large Bitcoin transactions'''
    # Implement your whale transaction query
    # Example: Query blockchain explorer API
    return {
        'transactions': [
            {
                'amount_btc': 150.5,
                'timestamp': datetime.now().isoformat(),
                'from_address': 'bc1q...',
                'to_address': 'bc1q...',
                'type': 'exchange_inflow'
            }
        ],
        'total_volume': 1250.5,
        'count': 8
    }

def query_narrative_shifts(platforms=None):
    '''Query social sentiment and trends'''
    # Implement social sentiment analysis
    return {
        'trending_topics': ['Bitcoin ETF', 'Institutional Adoption'],
        'sentiment_score': 0.72,
        'engagement_increase': 45.3
    }

def query_derivatives_signals(exchanges=None):
    '''Query derivatives market data'''
    # Implement derivatives data query
    return {
        'funding_rate': 0.0235,
        'open_interest_change': 12.5,
        'liquidations_24h': 125000000
    }

def lambda_handler(event, context):
    '''Main Lambda handler for Bedrock Agent action group'''
    
    agent = event.get('agent', {})
    action_group = event.get('actionGroup', '')
    function = event.get('function', '')
    parameters = event.get('parameters', [])
    
    # Convert parameters to dict
    params = {p['name']: p['value'] for p in parameters}
    
    # Route to appropriate function
    function_map = {
        'query_whale_movements': query_whale_movements,
        'query_narrative_shifts': query_narrative_shifts,
        'query_derivatives_signals': query_derivatives_signals,
        # Add other functions...
    }
    
    if function in function_map:
        result = function_map[function](**params)
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps(result)
                        }
                    }
                }
            }
        }
    else:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseState': 'FAILURE',
                    'responseBody': {
                        'TEXT': {
                            'body': f'Unknown function: {function}'
                        }
                    }
                }
            }
        }
"""


# Setup instructions
SETUP_INSTRUCTIONS = """
# Amazon Bedrock Agent Setup Instructions

## 1. Create IAM Role for Bedrock Agent

Create an IAM role with the following trust policy:

```json
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
```

Attach these policies:
- AmazonBedrockFullAccess (or custom policy with bedrock:InvokeModel)
- Custom policy for Lambda invocation
- Custom policy for S3 access (if using knowledge bases)

## 2. Create Lambda Function for Action Group

1. Create a new Lambda function with Python 3.12 runtime
2. Copy the Lambda function template code above
3. Configure timeout to 30 seconds
4. Add necessary permissions to invoke external APIs
5. Note the Lambda ARN for agent configuration

## 3. Create Bedrock Agent

Using AWS CLI:

```bash
aws bedrock-agent create-agent \\
  --agent-name MarketHunterAgent \\
  --foundation-model anthropic.claude-3-sonnet-20240229-v1:0 \\
  --instruction "$(cat agent_instruction.txt)" \\
  --agent-resource-role-arn arn:aws:iam::ACCOUNT:role/BedrockAgentRole
```

## 4. Create Action Group

```bash
aws bedrock-agent create-agent-action-group \\
  --agent-id YOUR_AGENT_ID \\
  --agent-version DRAFT \\
  --action-group-name MarketDataQueries \\
  --action-group-executor lambda=arn:aws:lambda:REGION:ACCOUNT:function:market-hunter-actions \\
  --api-schema file://action-group-schema.json
```

## 5. Create Agent Alias

```bash
aws bedrock-agent create-agent-alias \\
  --agent-id YOUR_AGENT_ID \\
  --agent-alias-name prod \\
  --description "Production alias for Market Hunter Agent"
```

## 6. Prepare and Associate Knowledge Base (Optional)

```bash
aws bedrock-agent create-knowledge-base \\
  --name BitcoinMarketKnowledge \\
  --role-arn arn:aws:iam::ACCOUNT:role/BedrockKBRole \\
  --knowledge-base-configuration type=VECTOR,vectorKnowledgeBaseConfiguration={embeddingModelArn=arn:aws:bedrock:REGION::foundation-model/amazon.titan-embed-text-v1}

aws bedrock-agent associate-agent-knowledge-base \\
  --agent-id YOUR_AGENT_ID \\
  --agent-version DRAFT \\
  --knowledge-base-id YOUR_KB_ID
```

## 7. Update Python Code

Update the example_usage.py file with your agent details:

```python
BEDROCK_AGENT_ID = "YOUR_AGENT_ID"
BEDROCK_AGENT_ALIAS_ID = "YOUR_ALIAS_ID"
AWS_REGION = "us-east-1"
```

## 8. Test the Agent

```bash
python src/example_usage.py
```

## Required AWS Permissions

Your IAM user/role needs:
- bedrock:InvokeAgent
- bedrock:GetAgent
- bedrock:CreateAgent
- lambda:InvokeFunction (for the action group Lambda)
- s3:GetObject (if using knowledge bases)

## Cost Considerations

- Bedrock Agent: Pay per request
- Claude 3 Sonnet: ~$0.003 per 1K input tokens, ~$0.015 per 1K output tokens
- Lambda: First 1M requests free, then $0.20 per 1M
- Knowledge Base (optional): Titan Embeddings pricing + vector store costs

## Monitoring

Set up CloudWatch alarms for:
- Agent invocation errors
- Lambda function errors
- Token usage and costs
- Response latency
"""

if __name__ == "__main__":
    print("Bedrock Agent Configuration")
    print("=" * 80)
    print(json.dumps(AGENT_CONFIGURATION, indent=2))
    print("\n" + "=" * 80)
    print("\nLambda Function Template")
    print("=" * 80)
    print(LAMBDA_FUNCTION_TEMPLATE)
    print("\n" + "=" * 80)
    print("\nSetup Instructions")
    print("=" * 80)
    print(SETUP_INSTRUCTIONS)
