# 🚀 Quick Start: NewsAPI Integration

## ⏱️ 5-Minute Setup

### Step 1: Get Your Free API Key (3 minutes)

1. Visit: **https://newsapi.org/register**
2. Fill in the form:
   - Email address
   - Choose "Individual" account type
   - Agree to terms
3. Click "Submit"
4. Check your email and verify
5. Go to dashboard and copy your API key

### Step 2: Add API Key to Environment (1 minute)

```bash
# Open .env file
nano .env

# Add your API key (replace with your actual key)
NEWSAPI_KEY=your_actual_api_key_here

# Save and exit (Ctrl+X, then Y, then Enter)
```

### Step 3: Test the Integration (1 minute)

```bash
python test_newsapi_fetch.py
```

**Expected Output:**
```
✓ API key found: abcd1234...xyz9
✓ NewsAPI is accessible
✓ Retrieved 15 articles
✓ Sentiment Analysis Complete

Results: 6/6 tests passed
🎉 All tests passed! NewsAPI integration is working correctly.
```

---

## 🎯 What You Get

### Real-Time News Sentiment

```python
# The agent now automatically receives:
{
  "overall_sentiment_score": 0.68,      # 0-1 scale (0.68 = bullish)
  "sentiment_classification": "Bullish",
  "confidence": 0.82,                    # How confident (0.82 = high)
  "article_count": 15,                   # Articles analyzed
  "bullish_count": 9,
  "bearish_count": 3,
  "neutral_count": 3
}
```

### 13 Major News Sources

- Bloomberg
- Reuters
- Wall Street Journal
- CNBC
- Financial Times
- CoinDesk
- CoinTelegraph
- Forbes
- Business Insider
- MarketWatch
- Decrypt
- The Block
- Bitcoin Magazine

---

## 📊 Rate Limits (Free Tier)

| Limit | Value |
|-------|-------|
| **Requests per day** | 100 |
| **Reset time** | Midnight UTC |
| **Historical data** | Last 30 days |
| **Cost** | **$0/month** |

**100 requests/day is sufficient for:**
- Hourly polling (24 requests/day)
- 4 requests per hour with headroom
- Development and testing
- Light production use

---

## 🧪 Test Commands

### Run Full Test Suite
```bash
python test_newsapi_fetch.py
```

### Quick Health Check
```python
import asyncio
from src.data_interfaces.newsapi_interface import NewsAPIInterface

async def quick_test():
    interface = NewsAPIInterface()
    health = await interface.health_check()
    print(f"Status: {health['status']}")
    print(f"Latency: {health['latency_ms']:.1f}ms")

asyncio.run(quick_test())
```

### Fetch Latest News
```bash
python -c "
import asyncio
from src.data_interfaces.newsapi_interface import NewsAPIInterface
from src.models.market_data import DataRequest, DataType, TimeFrame

async def test():
    interface = NewsAPIInterface()
    request = DataRequest(
        data_type=DataType.NEWS,
        symbol='BTC',
        timeframe=TimeFrame.HOUR_24
    )
    response = await interface.fetch(request)
    if response.success:
        print(f'Found {len(response.data[\"articles\"])} articles')
        for article in response.data['articles'][:3]:
            print(f'  - {article[\"title\"][:60]}...')
    else:
        print(f'Error: {response.error}')

asyncio.run(test())
"
```

---

## 🔧 Troubleshooting

### ❌ "NEWSAPI_KEY not found"

**Fix:**
```bash
# Check if .env exists
ls -la .env

# If missing, create it
cp .env.example .env

# Add your key
echo "NEWSAPI_KEY=your_key_here" >> .env
```

### ❌ "Authentication failed (401)"

**Causes:**
1. Invalid API key
2. Placeholder value still in .env
3. Key not activated yet (wait 5 mins after signup)

**Fix:**
```bash
# Verify key in .env
grep NEWSAPI_KEY .env

# Should show: NEWSAPI_KEY=<32-char-hex-string>
# If shows: NEWSAPI_KEY=your_newsapi_key_here (WRONG!)

# Get new key from: https://newsapi.org/account
```

### ❌ "Rate limit exceeded (429)"

**Fix:**
- Wait until midnight UTC for reset
- Reduce polling frequency
- Implement caching (already built-in: 60s)

### ❌ "No articles found"

**This is normal if:**
- Testing during quiet market hours
- Weekend with no news
- Holidays

**Verify manually:**
```bash
curl "https://newsapi.org/v2/everything?q=Bitcoin&apiKey=YOUR_KEY"
```

---

## 📈 What Happens Next

### Automatic Integration

Once your API key is configured, the BTC Agent will:

1. **Auto-discover** NewsAPI on startup (no code changes needed)
2. **Fetch news sentiment** every hour (configurable)
3. **Analyze sentiment** from 13 major sources
4. **Cache results** for 60 seconds (reduces API calls)
5. **Provide context** for price movements

### Example Agent Behavior

**Before NewsAPI:**
```
Price increased 5% → Unknown cause → Conservative action
```

**After NewsAPI:**
```
Price increased 5% 
→ News sentiment: 0.72 (Very Bullish)
→ Top story: "Bitcoin ETF approval imminent" (Bloomberg)
→ Agent adjusts: Bullish positioning
```

---

## 💡 Pro Tips

### 1. Monitor Your Usage

Check your remaining requests:
```bash
# In test output, look for:
# "Rate Limit: 100 requests/day"
# "Requests used today: 23/100"
```

### 2. Optimize Polling Frequency

```python
# Good: Hourly checks (24 requests/day)
polling_interval = 3600  # 1 hour

# Acceptable: Every 30 minutes (48 requests/day)
polling_interval = 1800  # 30 minutes

# Aggressive: Every 15 minutes (96 requests/day)
polling_interval = 900  # 15 minutes

# Too much: Every 5 minutes (288 requests/day) ❌ Exceeds limit
```

### 3. Use Built-in Caching

```python
# The manager automatically caches for 60 seconds
# Multiple requests within 60s = 1 API call

# Example:
response1 = await manager.fetch_data(...)  # API call
response2 = await manager.fetch_data(...)  # Cached (if within 60s)
response3 = await manager.fetch_data(...)  # Cached (if within 60s)
```

### 4. Check Sentiment Confidence

```python
if sentiment["confidence"] > 0.7:
    # High confidence - strong signal
    weight = 1.0
elif sentiment["confidence"] > 0.5:
    # Medium confidence - moderate signal
    weight = 0.6
else:
    # Low confidence - weak signal
    weight = 0.3
```

---

## 📚 Full Documentation

For complete details, see:
- **Implementation Guide**: `docs/NEWSAPI_IMPLEMENTATION.md`
- **Architecture Overview**: `docs/ARCHITECTURE_OVERVIEW.md`
- **Data Source Comparison**: `docs/DATA_SOURCE_COMPARISON.md`

---

## ✅ Verification Checklist

After completing the 5-minute setup:

- [ ] API key obtained from newsapi.org
- [ ] Key added to .env file
- [ ] Test suite passes (6/6 tests)
- [ ] Health check shows "healthy" status
- [ ] News articles fetch successfully
- [ ] Sentiment analysis working
- [ ] Latency < 500ms

**If all checked:** 🎉 You're ready to go!

---

## 🆘 Need Help?

### Check API Key Status
https://newsapi.org/account

### Test API Key Manually
```bash
curl "https://newsapi.org/v2/everything?q=Bitcoin&from=2025-01-01&apiKey=YOUR_KEY"
```

### View API Documentation
https://newsapi.org/docs/endpoints/everything

### Check API Status
https://status.newsapi.org

---

**Setup Time:** 5 minutes  
**Cost:** $0/month (free tier)  
**Data Coverage:** 33% (up from 25%)  
**Status:** ✅ Ready to test
