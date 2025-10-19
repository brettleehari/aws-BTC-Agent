# ✅ GitHub to AWS CI/CD Setup Checklist

Use this checklist to set up your automated deployment pipeline.

---

## 🎯 Phase 1: Prerequisites (5 minutes)

### AWS Setup
- [ ] AWS account created and active
- [ ] AWS CLI installed
  ```bash
  aws --version  # Should show version 2.x
  ```
- [ ] AWS credentials configured
  ```bash
  aws sts get-caller-identity  # Should show your account info
  ```
- [ ] Bedrock access enabled in your region
  ```bash
  aws bedrock list-foundation-models --region us-east-1
  ```

### GitHub Setup
- [ ] GitHub account with repo access
- [ ] GitHub CLI installed (optional but recommended)
  ```bash
  gh --version
  ```
- [ ] GitHub CLI authenticated (if installed)
  ```bash
  gh auth login
  ```

### Project Setup
- [ ] Repository cloned locally
- [ ] On `main` branch
  ```bash
  git branch  # Should show * main
  ```

---

## 🎯 Phase 2: IAM User Creation (5 minutes)

- [ ] Run the setup script
  ```bash
  cd /workspaces/aws-BTC-Agent
  ./setup-github-cicd.sh
  ```

- [ ] Script completed successfully
- [ ] Access keys displayed and saved
- [ ] File `.github-secrets.txt` created

**Important:** Copy these values now! You'll need them in the next step.

---

## 🎯 Phase 3: GitHub Secrets (3 minutes)

### Option A: Using GitHub CLI (Recommended)

If you have `gh` CLI and ran the setup script:
- [ ] Script asked to add secrets automatically
- [ ] You answered "Yes"
- [ ] Secrets added successfully

Verify:
```bash
gh secret list
```

Should show:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION` (optional)

### Option B: Manual Setup

1. [ ] Open GitHub repository in browser
2. [ ] Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. [ ] Click **"New repository secret"**

4. [ ] Add `AWS_ACCESS_KEY_ID`:
   - Name: `AWS_ACCESS_KEY_ID`
   - Secret: `AKIA...` (from `.github-secrets.txt`)
   - Click **Add secret**

5. [ ] Add `AWS_SECRET_ACCESS_KEY`:
   - Name: `AWS_SECRET_ACCESS_KEY`
   - Secret: `wJalr...` (from `.github-secrets.txt`)
   - Click **Add secret**

6. [ ] (Optional) Add `AWS_REGION`:
   - Name: `AWS_REGION`
   - Secret: `us-east-1` (or your preferred region)
   - Click **Add secret**

---

## 🎯 Phase 4: Enable Bedrock Models (2 minutes)

- [ ] Go to AWS Console
- [ ] Navigate to: **Amazon Bedrock** → **Model access**
- [ ] Click **Modify model access** or **Request access**
- [ ] Enable these models:
  - [ ] Anthropic Claude 3.5 Sonnet (Required)
  - [ ] Anthropic Claude 3 Haiku (Optional, for routing)
- [ ] Click **Save changes**
- [ ] Wait for status to show **"Access granted"** (usually instant)

Verify:
```bash
aws bedrock list-foundation-models --region us-east-1 \
  --by-provider anthropic | grep claude-3-5-sonnet
```

---

## 🎯 Phase 5: Verify Workflow Files (1 minute)

- [ ] Workflow file exists:
  ```bash
  ls -l .github/workflows/deploy-to-aws.yml
  ```
  Should show ~16KB file

- [ ] Test workflow file exists:
  ```bash
  ls -l .github/workflows/test.yml
  ```
  Should show file (optional)

- [ ] Setup script is executable:
  ```bash
  ls -l setup-github-cicd.sh
  ```
  Should show `-rwx` permissions

---

## 🎯 Phase 6: First Deployment (8-12 minutes)

### Commit and Push

- [ ] Delete sensitive file:
  ```bash
  rm .github-secrets.txt  # Important for security!
  ```

- [ ] Check git status:
  ```bash
  git status
  ```

- [ ] Stage all files:
  ```bash
  git add .
  ```

- [ ] Commit changes:
  ```bash
  git commit -m "Setup GitHub to AWS CI/CD pipeline"
  ```

- [ ] Push to main:
  ```bash
  git push origin main
  ```

### Monitor Deployment

- [ ] Open GitHub repository in browser
- [ ] Go to **Actions** tab
- [ ] Click on the running workflow: **"Deploy to AWS"**
- [ ] Watch the progress (takes 8-12 minutes)

### Expected Job Results
- [ ] ✅ **test** - Tests passed
- [ ] ✅ **build-lambda** - Lambda package built
- [ ] ✅ **deploy-dynamodb** - Tables created
- [ ] ✅ **deploy-lambda** - Lambda deployed
- [ ] ✅ **deploy-bedrock-agent** - Agent created/updated
- [ ] ✅ **verify-deployment** - Health checks passed
- [ ] ✅ **notify** - Success notification

---

## 🎯 Phase 7: Post-Deployment (2 minutes)

### Add Bedrock Agent ID

After first deployment:

- [ ] Check workflow logs for this line:
  ```
  ⚠️  Please add BEDROCK_AGENT_ID=AGENT123... to GitHub Secrets
  ```

- [ ] Copy the Agent ID value

- [ ] Add to GitHub Secrets:
  - Go to: **Settings** → **Secrets** → **New repository secret**
  - Name: `BEDROCK_AGENT_ID`
  - Secret: `AGENT123...` (from logs)
  - Click **Add secret**

Or using CLI:
```bash
echo "AGENT123..." | gh secret set BEDROCK_AGENT_ID
```

---

## 🎯 Phase 8: Verification (3 minutes)

### Verify AWS Resources

- [ ] DynamoDB tables created:
  ```bash
  aws dynamodb list-tables | grep agent_
  ```
  Should show 4 tables:
  - `agent_decisions`
  - `agent_memory_ltm`
  - `agent_state`
  - `agent_signals`

- [ ] Lambda function deployed:
  ```bash
  aws lambda get-function --function-name market-hunter-action-handler
  ```
  Should show function details

- [ ] Bedrock Agent created:
  ```bash
  aws bedrock-agent get-agent --agent-id $BEDROCK_AGENT_ID --region us-east-1
  ```
  Should show agent details

### Test the Pipeline

- [ ] Make a small change:
  ```bash
  echo "# CI/CD test" >> README.md
  git add README.md
  git commit -m "Test CI/CD pipeline"
  git push origin main
  ```

- [ ] Go to **Actions** tab
- [ ] Watch the deployment run again
- [ ] Verify it completes successfully

---

## 🎯 Phase 9: Security Cleanup (2 minutes)

- [ ] Delete `.github-secrets.txt` if still exists:
  ```bash
  rm .github-secrets.txt
  ```

- [ ] Verify it's in `.gitignore`:
  ```bash
  grep github-secrets .gitignore
  ```
  Should show: `.github-secrets.txt`

- [ ] Commit if `.gitignore` was updated:
  ```bash
  git add .gitignore
  git commit -m "Add .github-secrets.txt to .gitignore"
  git push origin main
  ```

---

## 🎯 Phase 10: Optional Enhancements

### Branch Protection

- [ ] Go to: **Settings** → **Branches** → **Add rule**
- [ ] Branch name pattern: `main`
- [ ] Enable:
  - [ ] Require pull request reviews before merging
  - [ ] Require status checks to pass before merging
  - [ ] Require branches to be up to date before merging
- [ ] Click **Create** or **Save changes**

### Notifications (Optional)

- [ ] Set up Slack webhook (if using Slack)
- [ ] Add webhook to GitHub Secrets as `SLACK_WEBHOOK`
- [ ] Update workflow to include Slack notifications

### Multi-Environment (Optional)

- [ ] Create `develop` branch for staging
- [ ] Create separate AWS accounts for dev/staging/prod
- [ ] Update workflow to deploy to different environments

---

## ✅ Success Criteria

Your CI/CD is fully set up when:

- [x] ✅ Setup script ran successfully
- [x] ✅ GitHub Secrets configured
- [x] ✅ Bedrock models enabled
- [x] ✅ First deployment completed
- [x] ✅ All AWS resources created
- [x] ✅ `BEDROCK_AGENT_ID` added to secrets
- [x] ✅ Test deployment successful
- [x] ✅ Security cleanup completed

---

## 📊 Current Status

**Setup Progress:** 0/10 phases complete

Update this as you go:
- [ ] Phase 1: Prerequisites
- [ ] Phase 2: IAM User Creation
- [ ] Phase 3: GitHub Secrets
- [ ] Phase 4: Enable Bedrock Models
- [ ] Phase 5: Verify Workflow Files
- [ ] Phase 6: First Deployment
- [ ] Phase 7: Post-Deployment
- [ ] Phase 8: Verification
- [ ] Phase 9: Security Cleanup
- [ ] Phase 10: Optional Enhancements

---

## 🆘 Troubleshooting

If something goes wrong, check:

1. **GitHub Actions logs** - Most errors have clear messages
2. **[Troubleshooting Guide](docs/GITHUB_AWS_CICD_SETUP.md#troubleshooting)** - Common issues and solutions
3. **AWS credentials** - Run `aws sts get-caller-identity`
4. **IAM permissions** - Check the deployment user has required policies
5. **Bedrock access** - Verify models are enabled

---

## 📚 Documentation

- **[Full Setup Guide](docs/GITHUB_AWS_CICD_SETUP.md)** - Comprehensive instructions
- **[Quick Reference](docs/CICD_QUICK_REFERENCE.md)** - Commands and tips
- **[Implementation Summary](CICD_IMPLEMENTATION_SUMMARY.md)** - What was created

---

## 🎉 Congratulations!

Once all phases are complete, you have:

✅ Fully automated deployment pipeline  
✅ Tests run on every commit  
✅ Deployment to AWS on every merge  
✅ Health checks and verification  
✅ Secure credential management  
✅ Rollback capability  

**No more manual deployments!** 🚀

---

**Estimated Total Time:** 25-35 minutes (one-time setup)  
**Future Deployments:** Automatic (8-12 minutes)  

**Last Updated:** October 19, 2025
