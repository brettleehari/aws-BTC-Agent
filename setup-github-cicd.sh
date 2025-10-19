#!/bin/bash
# Setup GitHub to AWS CI/CD Integration
# This script helps you configure GitHub Actions for automatic AWS deployment

set -e

echo "🔄 GitHub to AWS CI/CD Setup"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it first."
    echo "Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi
print_success "AWS CLI installed"

# Check gh CLI
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI not found. You'll need to add secrets manually."
    GH_CLI_AVAILABLE=false
else
    print_success "GitHub CLI installed"
    GH_CLI_AVAILABLE=true
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured"
    echo "Run: aws configure"
    exit 1
fi
print_success "AWS credentials configured"

echo ""
echo "================================"
echo "Step 1: Create IAM User for GitHub Actions"
echo "================================"
echo ""

read -p "Enter IAM username for GitHub Actions [github-actions-deployer]: " IAM_USER
IAM_USER=${IAM_USER:-github-actions-deployer}

# Check if user exists
if aws iam get-user --user-name "$IAM_USER" &> /dev/null; then
    print_warning "IAM user '$IAM_USER' already exists"
    read -p "Do you want to create new access keys for this user? (y/N): " CREATE_NEW_KEYS
    if [[ ! "$CREATE_NEW_KEYS" =~ ^[Yy]$ ]]; then
        echo "Using existing user. Make sure access keys are configured in GitHub."
        exit 0
    fi
else
    echo "Creating IAM user: $IAM_USER"
    if aws iam create-user --user-name "$IAM_USER" &> /dev/null; then
        print_success "IAM user created"
    else
        print_error "Failed to create IAM user"
        exit 1
    fi
fi

echo ""
echo "Attaching deployment policy..."

# Create policy document
cat > /tmp/github-deployer-policy.json << 'EOF'
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
        "iam:GetRole",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PutRolePolicy",
        "iam:PassRole",
        "iam:ListAttachedRolePolicies",
        "logs:*",
        "s3:*",
        "ssm:PutParameter",
        "ssm:GetParameter",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
EOF

if aws iam put-user-policy \
    --user-name "$IAM_USER" \
    --policy-name "DeploymentPolicy" \
    --policy-document file:///tmp/github-deployer-policy.json &> /dev/null; then
    print_success "Deployment policy attached"
else
    print_error "Failed to attach policy"
    exit 1
fi

echo ""
echo "================================"
echo "Step 2: Create Access Keys"
echo "================================"
echo ""

echo "Creating access keys..."
ACCESS_KEY_OUTPUT=$(aws iam create-access-key --user-name "$IAM_USER" 2>&1)

if [ $? -eq 0 ]; then
    ACCESS_KEY_ID=$(echo "$ACCESS_KEY_OUTPUT" | grep -o '"AccessKeyId": "[^"]*' | sed 's/"AccessKeyId": "//')
    SECRET_ACCESS_KEY=$(echo "$ACCESS_KEY_OUTPUT" | grep -o '"SecretAccessKey": "[^"]*' | sed 's/"SecretAccessKey": "//')
    
    print_success "Access keys created"
    echo ""
    print_warning "IMPORTANT: Save these credentials securely!"
    echo ""
    echo "AWS_ACCESS_KEY_ID: $ACCESS_KEY_ID"
    echo "AWS_SECRET_ACCESS_KEY: $SECRET_ACCESS_KEY"
    echo ""
    
    # Save to file for reference
    cat > .github-secrets.txt << EOF
# GitHub Secrets for CI/CD
# Add these to: GitHub Repo → Settings → Secrets and variables → Actions

AWS_ACCESS_KEY_ID=$ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=$SECRET_ACCESS_KEY
AWS_REGION=${AWS_REGION:-us-east-1}

# After first deployment, add:
# BEDROCK_AGENT_ID=<from deployment logs>
EOF
    
    print_success "Credentials saved to .github-secrets.txt"
else
    print_error "Failed to create access keys"
    echo "$ACCESS_KEY_OUTPUT"
    exit 1
fi

echo ""
echo "================================"
echo "Step 3: Configure GitHub Secrets"
echo "================================"
echo ""

if [ "$GH_CLI_AVAILABLE" = true ]; then
    read -p "Do you want to add secrets to GitHub now? (y/N): " ADD_SECRETS
    
    if [[ "$ADD_SECRETS" =~ ^[Yy]$ ]]; then
        echo ""
        print_info "Authenticating with GitHub..."
        
        if gh auth status &> /dev/null; then
            print_success "Already authenticated with GitHub"
        else
            gh auth login
        fi
        
        echo ""
        print_info "Adding secrets to GitHub repository..."
        
        # Add AWS_ACCESS_KEY_ID
        if echo "$ACCESS_KEY_ID" | gh secret set AWS_ACCESS_KEY_ID; then
            print_success "AWS_ACCESS_KEY_ID added"
        else
            print_error "Failed to add AWS_ACCESS_KEY_ID"
        fi
        
        # Add AWS_SECRET_ACCESS_KEY
        if echo "$SECRET_ACCESS_KEY" | gh secret set AWS_SECRET_ACCESS_KEY; then
            print_success "AWS_SECRET_ACCESS_KEY added"
        else
            print_error "Failed to add AWS_SECRET_ACCESS_KEY"
        fi
        
        # Add AWS_REGION (optional)
        AWS_REGION=${AWS_REGION:-us-east-1}
        if echo "$AWS_REGION" | gh secret set AWS_REGION; then
            print_success "AWS_REGION added ($AWS_REGION)"
        else
            print_warning "Failed to add AWS_REGION (optional)"
        fi
        
        echo ""
        print_success "GitHub secrets configured!"
    else
        echo ""
        print_info "Add secrets manually:"
        echo "1. Go to: GitHub Repo → Settings → Secrets and variables → Actions"
        echo "2. Click 'New repository secret'"
        echo "3. Add the secrets from .github-secrets.txt"
    fi
else
    echo ""
    print_info "Add secrets manually:"
    echo "1. Go to: GitHub Repo → Settings → Secrets and variables → Actions"
    echo "2. Click 'New repository secret'"
    echo "3. Add the secrets from .github-secrets.txt"
fi

echo ""
echo "================================"
echo "Step 4: Enable Bedrock Model Access"
echo "================================"
echo ""

print_info "Checking Bedrock model access..."
AWS_REGION=${AWS_REGION:-us-east-1}

if aws bedrock list-foundation-models --region "$AWS_REGION" &> /dev/null; then
    print_success "Bedrock accessible in $AWS_REGION"
    
    # Check for Claude 3.5 Sonnet
    if aws bedrock list-foundation-models --region "$AWS_REGION" \
        --by-provider anthropic | grep -q "claude-3-5-sonnet"; then
        print_success "Claude 3.5 Sonnet available"
    else
        print_warning "Claude 3.5 Sonnet may not be enabled"
        echo "Please enable it in AWS Console:"
        echo "AWS Bedrock → Model access → Request access to Anthropic models"
    fi
else
    print_warning "Could not verify Bedrock access"
    echo "Please verify manually in AWS Console"
fi

echo ""
echo "================================"
echo "Step 5: Verify Workflow Files"
echo "================================"
echo ""

if [ -f ".github/workflows/deploy-to-aws.yml" ]; then
    print_success "Deployment workflow found"
else
    print_error "Deployment workflow not found"
    echo "Expected: .github/workflows/deploy-to-aws.yml"
    exit 1
fi

if [ -f ".github/workflows/test.yml" ]; then
    print_success "Test workflow found"
else
    print_warning "Test workflow not found (optional)"
fi

echo ""
echo "================================"
echo "✅ Setup Complete!"
echo "================================"
echo ""

print_success "GitHub to AWS CI/CD is configured!"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Test the pipeline:"
echo "   git add ."
echo "   git commit -m \"Setup CI/CD pipeline\""
echo "   git push origin main"
echo ""
echo "2. Monitor deployment:"
echo "   GitHub → Actions → Deploy to AWS"
echo ""
echo "3. After first deployment:"
echo "   - Check logs for BEDROCK_AGENT_ID"
echo "   - Add it to GitHub Secrets"
echo ""
echo "4. View deployment guide:"
echo "   cat docs/GITHUB_AWS_CICD_SETUP.md"
echo ""

print_info "Important files created:"
echo "  - .github-secrets.txt (DELETE after adding to GitHub!)"
echo "  - .github/workflows/deploy-to-aws.yml"
echo ""

print_warning "Security reminder:"
echo "  - Delete .github-secrets.txt after adding secrets to GitHub"
echo "  - Rotate access keys every 90 days"
echo "  - Enable branch protection on main branch"
echo ""

# Add .github-secrets.txt to .gitignore
if [ -f ".gitignore" ]; then
    if ! grep -q ".github-secrets.txt" .gitignore; then
        echo ".github-secrets.txt" >> .gitignore
        print_success "Added .github-secrets.txt to .gitignore"
    fi
fi

echo "🎉 Ready to deploy!"
echo ""
