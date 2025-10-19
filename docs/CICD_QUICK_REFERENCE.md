# 🚀 GitHub → AWS CI/CD Quick Reference

## 🔄 Deployment Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     CODE CHANGE                              │
│  Developer pushes code to feature branch                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  CREATE PULL REQUEST                         │
│  GitHub automatically runs tests                             │
│  ✓ Unit tests                                                │
│  ✓ Integration tests                                         │
│  ✓ Goal alignment tests                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   MERGE TO MAIN                              │
│  Triggers automatic deployment workflow                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  BUILD & DEPLOY                              │
│  1. Run Tests              (1-2 min)                         │
│  2. Build Lambda Package   (1 min)                           │
│  3. Deploy DynamoDB        (2-3 min)                         │
│  4. Deploy Lambda          (1-2 min)                         │
│  5. Deploy Bedrock Agent   (2-3 min)                         │
│  6. Verify Deployment      (1 min)                           │
│                                                              │
│  Total Time: 8-12 minutes                                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ✅ DEPLOYED TO AWS                              │
│  • Lambda function updated                                   │
│  • DynamoDB tables ready                                     │
│  • Bedrock Agent prepared                                    │
│  • All services verified                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Setup Checklist

### One-Time Setup (15 minutes)

- [ ] **Step 1: Run setup script**
  ```bash
  ./setup-github-cicd.sh
  ```

- [ ] **Step 2: Add GitHub Secrets**
  - Go to: `GitHub Repo → Settings → Secrets and variables → Actions`
  - Add: `AWS_ACCESS_KEY_ID`
  - Add: `AWS_SECRET_ACCESS_KEY`
  - Add: `AWS_REGION` (optional, defaults to us-east-1)

- [ ] **Step 3: Enable Bedrock Models**
  - AWS Console → Amazon Bedrock → Model access
  - Request access to: Anthropic Claude 3.5 Sonnet

- [ ] **Step 4: First Deployment**
  ```bash
  git add .
  git commit -m "Setup CI/CD"
  git push origin main
  ```

- [ ] **Step 5: Add Bedrock Agent ID**
  - Check GitHub Actions logs for: `BEDROCK_AGENT_ID=AGENT...`
  - Add to GitHub Secrets as: `BEDROCK_AGENT_ID`

---

## 🔧 Common Commands

### Check Deployment Status
```bash
# View recent deployments
gh run list --workflow=deploy-to-aws.yml --limit 5

# Watch current deployment
gh run watch
```

### Manual Deployment
```bash
# Trigger via GitHub CLI
gh workflow run deploy-to-aws.yml

# Or via GitHub UI
# Actions → Deploy to AWS → Run workflow
```

### Rollback
```bash
# Revert last commit
git revert HEAD
git push origin main

# Or deploy specific version
gh workflow run deploy-to-aws.yml --ref <commit-sha>
```

### View Logs
```bash
# Latest deployment logs
gh run view --log

# Specific workflow run
gh run view <run-id> --log
```

---

## 📊 What Gets Deployed

| Component | What Happens | Time |
|-----------|--------------|------|
| **Tests** | All tests run automatically | 1-2 min |
| **Lambda** | Function code updated, new version published | 1-2 min |
| **DynamoDB** | Tables created/updated if schema changed | 2-3 min |
| **Bedrock Agent** | Agent configuration updated, re-prepared | 2-3 min |
| **Verification** | Health checks run on all services | 1 min |

---

## 🔐 GitHub Secrets Required

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | IAM user access key | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key | `wJalr...` |
| `AWS_REGION` | AWS region (optional) | `us-east-1` |
| `BEDROCK_AGENT_ID` | Bedrock Agent ID (after first deploy) | `AGENT123...` |

---

## 🚨 Troubleshooting

### Deployment Failed

1. **Check logs**
   ```bash
   gh run view --log
   ```

2. **Common causes:**
   - ❌ AWS credentials expired → Rotate keys
   - ❌ Bedrock model not enabled → Enable in console
   - ❌ IAM permissions missing → Re-run setup script
   - ❌ Tests failed → Fix failing tests

### Tests Failed

```bash
# Run tests locally
pytest tests/ -v

# Run specific test
pytest tests/test_goal_alignment.py -v
```

### Lambda Update Failed

```bash
# Check Lambda status
aws lambda get-function --function-name market-hunter-action-handler

# View Lambda logs
aws logs tail /aws/lambda/market-hunter-action-handler --follow
```

---

## 🎯 Workflow Files

### `.github/workflows/deploy-to-aws.yml`
Main deployment workflow that runs on push to `main`

**Triggers:**
- Push to `main` branch
- Manual trigger via Actions UI

**Jobs:**
1. `test` - Run all tests
2. `build-lambda` - Build deployment package
3. `deploy-dynamodb` - Update DynamoDB tables
4. `deploy-lambda` - Deploy Lambda function
5. `deploy-bedrock-agent` - Update Bedrock Agent
6. `verify-deployment` - Health checks
7. `notify` - Send notifications

### `.github/workflows/test.yml`
Test workflow that runs on PRs

**Triggers:**
- Pull requests to `main` or `develop`
- Push to `develop` branch

**Jobs:**
1. `goal-alignment` - Goal alignment tests
2. `unit-tests` - Unit tests
3. `integration-tests` - Integration tests
4. `memory-tests` - Memory system tests

---

## 📈 Monitoring

### View Deployment History
```bash
# Last 10 deployments
gh run list --workflow=deploy-to-aws.yml --limit 10

# Filter by status
gh run list --workflow=deploy-to-aws.yml --status success
gh run list --workflow=deploy-to-aws.yml --status failure
```

### Check AWS Resources
```bash
# Lambda function
aws lambda get-function --function-name market-hunter-action-handler

# DynamoDB tables
aws dynamodb list-tables | grep agent_

# Bedrock Agent
aws bedrock-agent get-agent --agent-id $BEDROCK_AGENT_ID
```

### Cost Monitoring
```bash
# Estimated monthly costs
aws ce get-cost-and-usage \
  --time-period Start=$(date -d '1 month ago' +%Y-%m-%d),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

---

## 🎉 Success Indicators

After deployment completes, verify:

- ✅ GitHub Actions shows green checkmark
- ✅ No error logs in workflow output
- ✅ Lambda function state is "Active"
- ✅ DynamoDB tables are "ACTIVE"
- ✅ Bedrock Agent status is "PREPARED"
- ✅ Health check passed

---

## 📚 Additional Resources

- **Full Setup Guide:** [`docs/GITHUB_AWS_CICD_SETUP.md`](./GITHUB_AWS_CICD_SETUP.md)
- **Deployment Guide:** [`docs/AWS_DEPLOYMENT_COMPLETE.md`](./AWS_DEPLOYMENT_COMPLETE.md)
- **Architecture:** [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)
- **GitHub Actions Docs:** https://docs.github.com/en/actions

---

## 💡 Pro Tips

1. **Enable branch protection** on `main` to require PR reviews
2. **Set up Slack/Discord notifications** for deployment status
3. **Use environments** for production approval gates
4. **Rotate AWS keys** every 90 days
5. **Monitor costs** with AWS Cost Explorer
6. **Tag resources** for better cost tracking
7. **Use separate AWS accounts** for dev/staging/prod

---

**Last Updated:** October 2025  
**Estimated Setup Time:** 15 minutes  
**Deployment Time:** 8-12 minutes per deployment
