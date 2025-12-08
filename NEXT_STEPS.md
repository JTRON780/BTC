# 🎉 Workflow Ran Successfully! What's Next?

Congratulations! Your GitHub Actions pipeline has completed successfully. Here's what to do now:

---

## ✅ What Just Happened

Your automated pipeline just:
1. ✅ Collected news articles and Reddit posts about Bitcoin
2. ✅ Analyzed sentiment using FinBERT NLP model
3. ✅ Created hourly sentiment indices
4. ✅ Created daily sentiment indices
5. ✅ Saved the database as an artifact

---

## 📊 Step 1: Download and View Your Data

### Option A: Download Database from GitHub Actions

1. **Go to your GitHub repository**
2. **Click "Actions" tab**
3. **Click on the latest workflow run**
4. **Scroll down to "Artifacts" section**
5. **Click "database" to download**
6. **Extract the `btc_sentiment.db` file**

### Option B: View Data Directly

You can query the database to see what was collected:

```bash
# If you have sqlite3 installed
sqlite3 btc_sentiment.db

# Check raw items collected
SELECT COUNT(*) FROM raw_items;

# Check scored items
SELECT COUNT(*) FROM scored_items;

# Check sentiment indices
SELECT COUNT(*) FROM sentiment_indices;

# View latest sentiment indices
SELECT ts, granularity, raw_value, smoothed_value, n_posts 
FROM sentiment_indices 
ORDER BY ts DESC 
LIMIT 10;

# Exit sqlite
.exit
```

---

## 🚀 Step 2: Run Your Dashboard Locally

To visualize the sentiment data:

### Quick Start:

```bash
# 1. Make sure you have the database
# (Download from GitHub Actions artifacts, or it will create a new one)

# 2. Start the API server
uvicorn src.api.main:app --reload

# 3. In another terminal, start the dashboard
streamlit run src/app/dashboard.py
```

### Access:
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🔄 Step 3: Understanding the Automated System

### How It Works Now:

1. **GitHub Actions runs automatically every hour**
   - Collects new data
   - Scores sentiment
   - Updates indices
   - Saves database as artifact

2. **Database Persistence:**
   - Each run downloads the previous database
   - Adds new data to it
   - Uploads updated database
   - Database persists for 7 days as artifact

3. **To Use Fresh Data:**
   - Download latest database artifact
   - Replace your local `btc_sentiment.db`
   - Restart API/dashboard

---

## 📈 Step 4: View Sentiment Data via API

### Test the API Endpoints:

```bash
# Get sentiment indices (last 7 days, daily)
curl http://localhost:8000/api/v1/sentiment/?granularity=daily&days=7

# Get sentiment indices (last 24 hours, hourly)
curl http://localhost:8000/api/v1/sentiment/?granularity=hourly&days=1

# Get latest sentiment
curl http://localhost:8000/api/v1/sentiment/latest

# Get top drivers for today
curl "http://localhost:8000/api/v1/drivers/?day=$(date +%Y-%m-%d)"

# Health check
curl http://localhost:8000/api/v1/health/
```

---

## 🎯 Step 5: Set Up Continuous Monitoring

### Option A: Keep Using GitHub Actions (Current Setup)

**Pros:**
- ✅ Free for public repos
- ✅ Runs automatically every hour
- ✅ No server needed

**Cons:**
- Database stored as artifact (7-day retention)
- Need to download manually to view
- No persistent dashboard

**Best for:** Data collection and periodic analysis

---

### Option B: Deploy Dashboard to Cloud

**Recommended:** Deploy to Render.com or Railway.app

**Benefits:**
- ✅ Dashboard always accessible
- ✅ Persistent database
- ✅ Automatic updates
- ✅ Shareable URL

**See `DEPLOYMENT.md` for full instructions**

---

## 🔍 Step 6: Verify Your Data

### Check What Was Collected:

```python
# Quick Python script to check data
import sqlite3
from datetime import datetime

conn = sqlite3.connect('btc_sentiment.db')
cursor = conn.cursor()

# Count items
print("Raw items:", cursor.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0])
print("Scored items:", cursor.execute("SELECT COUNT(*) FROM scored_items").fetchone()[0])
print("Sentiment indices:", cursor.execute("SELECT COUNT(*) FROM sentiment_indices").fetchone()[0])

# Latest sentiment
latest = cursor.execute("""
    SELECT ts, granularity, raw_value, smoothed_value, n_posts 
    FROM sentiment_indices 
    ORDER BY ts DESC 
    LIMIT 1
""").fetchone()

if latest:
    print(f"\nLatest sentiment ({latest[1]}):")
    print(f"  Time: {latest[0]}")
    print(f"  Raw: {latest[2]:.3f}")
    print(f"  Smoothed: {latest[3]:.3f}")
    print(f"  Posts: {latest[4]}")

conn.close()
```

---

## 📝 Step 7: Customize Your Setup

### Adjust Collection Frequency:

Edit `.github/workflows/pipeline.yml`:

```yaml
schedule:
  - cron: '0 * * * *'  # Every hour (current)
  # - cron: '0 */2 * * *'  # Every 2 hours
  # - cron: '0 0 * * *'    # Once per day
```

### Add More Data Sources:

Edit your GitHub Secrets:
- `NEWS_FEEDS`: Add more RSS feeds
- `REDDIT_FEEDS`: Add more subreddits

### Change Retention:

Edit artifact retention in workflow:
```yaml
retention-days: 7  # Change to 30 for longer retention
```

---

## 🎨 Step 8: Explore the Dashboard

Once dashboard is running:

1. **KPI Cards** - See current sentiment, 24h/7d changes
2. **Trend Charts** - Visualize sentiment over time
3. **Gauge Chart** - Current sentiment visualization
4. **Top Drivers** - Most positive/negative content

**Try:**
- Switch between hourly/daily granularity
- Adjust time range slider
- Select different dates for top drivers
- Explore the interactive charts

---

## 🐛 Troubleshooting

### No Data Showing?

1. **Check if pipelines ran:**
   - Go to Actions tab
   - Verify latest run succeeded
   - Check logs for errors

2. **Verify database exists:**
   ```bash
   ls -lh btc_sentiment.db
   ```

3. **Check API is running:**
   ```bash
   curl http://localhost:8000/api/v1/health/
   ```

4. **Check database has data:**
   ```bash
   sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM sentiment_indices;"
   ```

### Dashboard Shows "No Data Available"?

- Make sure API is running
- Check database has sentiment indices
- Verify date range in sidebar
- Check API logs for errors

---

## 🚀 Next Steps Summary

1. ✅ **Download database** from GitHub Actions artifacts
2. ✅ **Start API**: `uvicorn src.api.main:app --reload`
3. ✅ **Start Dashboard**: `streamlit run src.app.dashboard.py`
4. ✅ **Explore data** at http://localhost:8501
5. ✅ **Optional**: Deploy to cloud for persistent access

---

## 📚 Additional Resources

- **How sentiment index works**: See `SENTIMENT_INDEX_EXPLAINED.md`
- **Deployment options**: See `DEPLOYMENT.md`
- **Automation setup**: See `AUTOMATION_SETUP.md`
- **API documentation**: http://localhost:8000/docs (when API is running)

---

## 🎉 You're All Set!

Your sentiment analysis system is now:
- ✅ Collecting data automatically every hour
- ✅ Analyzing sentiment with AI
- ✅ Creating time-series indices
- ✅ Ready to visualize!

**Enjoy exploring Bitcoin sentiment!** 📊₿

