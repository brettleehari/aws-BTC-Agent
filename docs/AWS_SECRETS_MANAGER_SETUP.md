# AWS Secrets Manager Migration Plan

## Overview

Migrate sensitive credentials from local `.env` files to AWS Secrets Manager for secure production deployment.

## Current State

Currently, sensitive credentials are stored in `.env` file (gitignored):

```
TWITTER_API_KEY=LhfjYRaut8v4UKKAyTNXjeiTS
TWITTER_API_SECRET=vPA3SxWGiL7gJcgOtlaoVJnxI030c32wwhGZp8bOjzhem4hQPH
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAA...
TWITTER_ACCESS_TOKEN=1979951904055590912-...
TWITTER_ACCESS_TOKEN_SECRET=L8W5dlwzojN...
```

**Security Issues:**
- ❌ Credentials stored in plaintext on local machine
- ❌ Must be manually configured on each deployment
- ❌ No audit trail for credential access
- ❌ No automatic rotation capability

## Target State

All credentials stored in AWS Secrets Manager with:

- ✅ Encrypted at rest (AES-256)
- ✅ Encrypted in transit (TLS)
- ✅ Automatic rotation support
- ✅ Access audit logging via CloudTrail
- ✅ Fine-grained IAM permissions
- ✅ Multi-region replication (optional)

## Migration Steps

### Phase 1: Create Secrets in AWS

#### Step 1.1: Create Twitter Credentials Secret

```bash
# Create secret for Twitter API credentials
aws secretsmanager create-secret \
    --name btc-agent/twitter/credentials \
    --description "Twitter API credentials for BTC Market Hunter Agent" \
    --secret-string '{
        "api_key": "LhfjYRaut8v4UKKAyTNXjeiTS",
        "api_secret": "vPA3SxWGiL7gJcgOtlaoVJnxI030c32wwhGZp8bOjzhem4hQPH",
        "bearer_token": "AAAAAAAAAAAAAAAAAAAAAGSq4wEAAAAAqpfE1GmacdBIeQ1D%2B2y%2FYV1hJx8%3DunBTuaZ4N6AXXJe8yANJShkwfHgIN3WctIayIQcEy9jftoeq6T",
        "access_token": "1979951904055590912-vYNTDfjk5DzArCC5qzfyP1SyNEznEk",
        "access_token_secret": "L8W5dlwzojNPcT6p6DphTO9OpQ7Qcyhkm88qXivbKPOqZ"
    }' \
    --region us-east-1
```

#### Step 1.2: Create Other API Credentials (Future)

```bash
# CoinGecko API Key (when needed)
aws secretsmanager create-secret \
    --name btc-agent/coingecko/api-key \
    --description "CoinGecko Pro API Key" \
    --secret-string '{"api_key": "your-coingecko-api-key"}' \
    --region us-east-1

# Glassnode API Key
aws secretsmanager create-secret \
    --name btc-agent/glassnode/api-key \
    --description "Glassnode API Key" \
    --secret-string '{"api_key": "your-glassnode-api-key"}' \
    --region us-east-1
```

### Phase 2: Update IAM Permissions

#### Step 2.1: Create IAM Policy for Lambda

Create policy `btc-agent-secrets-access-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadTwitterCredentials",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:btc-agent/twitter/*",
        "arn:aws:secretsmanager:us-east-1:*:secret:btc-agent/coingecko/*",
        "arn:aws:secretsmanager:us-east-1:*:secret:btc-agent/glassnode/*"
      ]
    },
    {
      "Sid": "DecryptSecrets",
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:DescribeKey"
      ],
      "Resource": "arn:aws:kms:us-east-1:*:key/*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "secretsmanager.us-east-1.amazonaws.com"
        }
      }
    }
  ]
}
```

#### Step 2.2: Attach Policy to Lambda Role

```bash
# Create the policy
aws iam create-policy \
    --policy-name BTCAgentSecretsAccessPolicy \
    --policy-document file://btc-agent-secrets-access-policy.json

# Attach to Lambda execution role
aws iam attach-role-policy \
    --role-name BTCAgentLambdaExecutionRole \
    --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/BTCAgentSecretsAccessPolicy
```

### Phase 3: Update Lambda Code

#### Step 3.1: Create Secrets Manager Helper Module

Create `src/utils/secrets_manager.py`:

```python
"""AWS Secrets Manager helper for retrieving credentials"""

import json
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """Helper class for AWS Secrets Manager"""
    
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region_name)
        self._cache = {}
    
    def get_secret(self, secret_name: str) -> dict:
        """
        Retrieve secret from AWS Secrets Manager.
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Dictionary with secret values
        """
        # Check cache first
        if secret_name in self._cache:
            logger.debug(f"Using cached secret: {secret_name}")
            return self._cache[secret_name]
        
        try:
            logger.info(f"Fetching secret from AWS: {secret_name}")
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse secret string
            secret = json.loads(response['SecretString'])
            
            # Cache it
            self._cache[secret_name] = secret
            
            return secret
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret not found: {secret_name}")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret: {secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret: {secret_name}")
            elif error_code == 'DecryptionFailure':
                logger.error(f"Cannot decrypt secret: {secret_name}")
            elif error_code == 'InternalServiceError':
                logger.error(f"AWS internal error fetching secret: {secret_name}")
            else:
                logger.error(f"Unknown error fetching secret {secret_name}: {e}")
            
            raise
    
    def get_twitter_credentials(self) -> dict:
        """Get Twitter API credentials"""
        return self.get_secret('btc-agent/twitter/credentials')
    
    def get_coingecko_api_key(self) -> str:
        """Get CoinGecko API key"""
        secret = self.get_secret('btc-agent/coingecko/api-key')
        return secret.get('api_key', '')
    
    def get_glassnode_api_key(self) -> str:
        """Get Glassnode API key"""
        secret = self.get_secret('btc-agent/glassnode/api-key')
        return secret.get('api_key', '')

# Global instance
_secrets_manager = None

def get_secrets_manager() -> SecretsManager:
    """Get or create global SecretsManager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager
```

#### Step 3.2: Update Twitter Interface

Modify `src/data_interfaces/twitter_interface.py`:

```python
import os
from .utils.secrets_manager import get_secrets_manager

class TwitterInterface(DataInterface):
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        super().__init__(api_key, config)
        
        # Try to load from environment first (local dev)
        if os.getenv('TWITTER_BEARER_TOKEN'):
            self.bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            self.api_key = os.getenv('TWITTER_API_KEY')
            self.api_secret = os.getenv('TWITTER_API_SECRET')
            self.access_token = os.getenv('TWITTER_ACCESS_TOKEN')
            self.access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        else:
            # Load from AWS Secrets Manager (production)
            try:
                secrets = get_secrets_manager().get_twitter_credentials()
                self.bearer_token = secrets['bearer_token']
                self.api_key = secrets['api_key']
                self.api_secret = secrets['api_secret']
                self.access_token = secrets['access_token']
                self.access_token_secret = secrets['access_token_secret']
            except Exception as e:
                logger.error(f"Failed to load Twitter credentials: {e}")
                raise ValueError("Twitter credentials not available")
```

### Phase 4: Update CloudFormation Template

Add Secrets Manager configuration to `infrastructure/cloudformation/bedrock-agent.yaml`:

```yaml
Resources:
  # Twitter Credentials Secret
  TwitterCredentialsSecret:
    Type: AWS::SecretsManager::Secret
    Properties:
      Name: btc-agent/twitter/credentials
      Description: Twitter API credentials for BTC Market Hunter Agent
      SecretString: !Sub |
        {
          "api_key": "${TwitterApiKey}",
          "api_secret": "${TwitterApiSecret}",
          "bearer_token": "${TwitterBearerToken}",
          "access_token": "${TwitterAccessToken}",
          "access_token_secret": "${TwitterAccessTokenSecret}"
        }
      KmsKeyId: !Ref SecretsEncryptionKey

  # KMS Key for Secrets Encryption
  SecretsEncryptionKey:
    Type: AWS::KMS::Key
    Properties:
      Description: KMS key for encrypting BTC Agent secrets
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Sid: Enable IAM User Permissions
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'
          - Sid: Allow Lambda to decrypt
            Effect: Allow
            Principal:
              AWS: !GetAtt ActionGroupLambdaExecutionRole.Arn
            Action:
              - 'kms:Decrypt'
              - 'kms:DescribeKey'
            Resource: '*'

  # Update Lambda Execution Role
  ActionGroupLambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      # ... existing properties ...
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: SecretsManagerAccess
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - secretsmanager:GetSecretValue
                  - secretsmanager:DescribeSecret
                Resource:
                  - !Ref TwitterCredentialsSecret
              - Effect: Allow
                Action:
                  - kms:Decrypt
                Resource: !GetAtt SecretsEncryptionKey.Arn

Parameters:
  TwitterApiKey:
    Type: String
    NoEcho: true
    Description: Twitter API Key
  TwitterApiSecret:
    Type: String
    NoEcho: true
    Description: Twitter API Secret
  TwitterBearerToken:
    Type: String
    NoEcho: true
    Description: Twitter Bearer Token
  TwitterAccessToken:
    Type: String
    NoEcho: true
    Description: Twitter Access Token
  TwitterAccessTokenSecret:
    Type: String
    NoEcho: true
    Description: Twitter Access Token Secret
```

### Phase 5: Update GitHub Actions

Update `.github/workflows/deploy-to-aws.yml` to use GitHub Secrets:

```yaml
env:
  AWS_REGION: us-east-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      # ... existing steps ...
      
      - name: Deploy CloudFormation Stack
        run: |
          aws cloudformation deploy \
            --template-file infrastructure/cloudformation/bedrock-agent.yaml \
            --stack-name btc-market-hunter-agent \
            --parameter-overrides \
              TwitterApiKey=${{ secrets.TWITTER_API_KEY }} \
              TwitterApiSecret=${{ secrets.TWITTER_API_SECRET }} \
              TwitterBearerToken=${{ secrets.TWITTER_BEARER_TOKEN }} \
              TwitterAccessToken=${{ secrets.TWITTER_ACCESS_TOKEN }} \
              TwitterAccessTokenSecret=${{ secrets.TWITTER_ACCESS_TOKEN_SECRET }} \
            --capabilities CAPABILITY_IAM \
            --region ${{ env.AWS_REGION }}
```

### Phase 6: Configure GitHub Secrets

Add secrets to GitHub repository:

```bash
# Using GitHub CLI
gh secret set TWITTER_API_KEY --body "LhfjYRaut8v4UKKAyTNXjeiTS"
gh secret set TWITTER_API_SECRET --body "vPA3SxWGiL7gJcgOtlaoVJnxI030c32wwhGZp8bOjzhem4hQPH"
gh secret set TWITTER_BEARER_TOKEN --body "AAAAAAAAAAAAAAAA..."
gh secret set TWITTER_ACCESS_TOKEN --body "1979951904055590912-..."
gh secret set TWITTER_ACCESS_TOKEN_SECRET --body "L8W5dlwzojN..."

# Or manually through GitHub UI:
# Repository → Settings → Secrets and variables → Actions → New repository secret
```

## Security Best Practices

### 1. Secret Rotation

Set up automatic rotation for Twitter credentials:

```bash
aws secretsmanager rotate-secret \
    --secret-id btc-agent/twitter/credentials \
    --rotation-lambda-arn arn:aws:lambda:us-east-1:ACCOUNT_ID:function:TwitterCredentialRotation \
    --rotation-rules AutomaticallyAfterDays=90
```

### 2. Access Monitoring

Enable CloudTrail logging:

```bash
# Create CloudTrail for Secrets Manager access
aws cloudtrail create-trail \
    --name btc-agent-secrets-audit \
    --s3-bucket-name btc-agent-audit-logs

# Enable event selector for Secrets Manager
aws cloudtrail put-event-selectors \
    --trail-name btc-agent-secrets-audit \
    --event-selectors '[{
        "ReadWriteType": "All",
        "IncludeManagementEvents": true,
        "DataResources": [{
            "Type": "AWS::SecretsManager::Secret",
            "Values": ["arn:aws:secretsmanager:us-east-1:*:secret:btc-agent/*"]
        }]
    }]'
```

### 3. Least Privilege Access

Only grant access to specific secrets:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:btc-agent/twitter/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

### 4. Secret Versioning

Secrets Manager maintains version history automatically. Rollback if needed:

```bash
# List secret versions
aws secretsmanager list-secret-version-ids \
    --secret-id btc-agent/twitter/credentials

# Get specific version
aws secretsmanager get-secret-value \
    --secret-id btc-agent/twitter/credentials \
    --version-id PREVIOUS_VERSION_ID
```

## Migration Checklist

- [ ] **Phase 1**: Create secrets in AWS Secrets Manager
  - [ ] Create Twitter credentials secret
  - [ ] Test secret retrieval with AWS CLI
  - [ ] Verify encryption (should use AWS managed key or custom KMS key)

- [ ] **Phase 2**: Update IAM permissions
  - [ ] Create IAM policy for secret access
  - [ ] Attach policy to Lambda execution role
  - [ ] Test policy with AWS Policy Simulator

- [ ] **Phase 3**: Update Lambda code
  - [ ] Create SecretsManager helper module
  - [ ] Update TwitterInterface to use Secrets Manager
  - [ ] Add fallback to environment variables for local dev
  - [ ] Test locally with mocked Secrets Manager

- [ ] **Phase 4**: Update CloudFormation template
  - [ ] Add Secrets Manager resources
  - [ ] Add KMS key for encryption
  - [ ] Update Lambda role with secret permissions
  - [ ] Add CloudFormation parameters

- [ ] **Phase 5**: Update GitHub Actions
  - [ ] Add GitHub Secrets
  - [ ] Update deployment workflow
  - [ ] Test deployment pipeline

- [ ] **Phase 6**: Security hardening
  - [ ] Enable secret rotation
  - [ ] Enable CloudTrail logging
  - [ ] Set up CloudWatch alarms for unauthorized access
  - [ ] Document emergency rollback procedure

- [ ] **Phase 7**: Cleanup
  - [ ] Remove credentials from `.env` file (keep template)
  - [ ] Update documentation
  - [ ] Verify no credentials in git history
  - [ ] Test production deployment

## Cost Estimate

**AWS Secrets Manager Pricing:**
- $0.40 per secret per month
- $0.05 per 10,000 API calls

**Expected Monthly Cost:**
- 3 secrets (Twitter, CoinGecko, Glassnode): $1.20/month
- API calls (~1M calls/month): $5.00/month
- **Total: ~$6.20/month**

**CloudTrail Logging (Optional):**
- First trail is free for management events
- Data events: $2.00 per 100,000 events

## Rollback Plan

If migration fails:

1. **Immediate Rollback:**
   ```bash
   # Revert Lambda to use environment variables
   aws lambda update-function-configuration \
       --function-name BTCAgentActionGroup \
       --environment Variables={
           TWITTER_BEARER_TOKEN=xxx,
           TWITTER_API_KEY=xxx
       }
   ```

2. **Emergency Access:**
   - Keep `.env` file locally until migration is validated
   - Don't delete local credentials for 30 days

3. **Monitoring:**
   - Set up CloudWatch alarms for Lambda errors
   - Monitor secret access patterns

## Testing Strategy

### Local Testing

```python
# Test with environment variables (.env file)
python test_twitter_fetch.py

# Test with mocked Secrets Manager
import boto3
from moto import mock_secretsmanager

@mock_secretsmanager
def test_twitter_with_secrets_manager():
    # Create mock secret
    client = boto3.client('secretsmanager', region_name='us-east-1')
    client.create_secret(
        Name='btc-agent/twitter/credentials',
        SecretString='{"bearer_token": "test_token"}'
    )
    
    # Test TwitterInterface
    twitter = TwitterInterface()
    assert twitter.bearer_token == "test_token"
```

### Production Testing

```bash
# Invoke Lambda to test secret retrieval
aws lambda invoke \
    --function-name BTCAgentActionGroup \
    --payload '{"action": "test_twitter_connection"}' \
    response.json

cat response.json
```

## Timeline

- **Week 1**: Create secrets and IAM policies
- **Week 2**: Update Lambda code and test locally
- **Week 3**: Update CloudFormation and deploy to staging
- **Week 4**: Production deployment and monitoring
- **Week 5**: Cleanup and documentation

## Support Contacts

- **AWS Support**: https://console.aws.amazon.com/support
- **Twitter Developer Platform**: https://developer.twitter.com/en/support
- **Internal Team**: Your team contact info

## References

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Lambda Environment Variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html)
- [Twitter API Security](https://developer.twitter.com/en/docs/authentication/oauth-2-0)
