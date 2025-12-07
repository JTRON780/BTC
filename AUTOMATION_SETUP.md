# Quick Start: Automated Pipeline Scheduling

## 🎯 What I've Set Up

I've created an automated scheduling system that will run your pipelines continuously. However, **GitHub Pages cannot run Python applications** - it only hosts static websites.

Instead, I've set up **GitHub Actions** which will run your pipelines automatically every hour, and provided deployment options for hosting your dashboard.

---

## ✅ What's Been Added

1. **`src/pipelines/scheduler.py`** - Automated pipeline runner
2. **`.github/workflows/pipeline.yml`** - GitHub Actions workflow (runs every hour)
3. **`DEPLOYMENT.md`** - Complete deployment guide
4. **Updated `requirements.txt`** - Added dependencies

---

## 🚀 Quick Start Options

### Option A: GitHub Actions (Free, Automated) ⭐ RECOMMENDED

**This runs your pipelines automatically every hour on GitHub's servers.**

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add automated pipeline scheduling"
   git push origin main
   ```

2. **Set up GitHub Secrets:**
   - Go to your repo: `Settings > Secrets and variables > Actions`
   - Click "New repository secret"
   - Add these secrets:
     ```
     NEWS_FEEDS=https://cointelegraph.com/rss,https://decrypt.co/feed
     REDDIT_FEEDS=bitcoin,cryptocurrency
     COINGECKO_BASE=https://api.coingecko.com/api/v3
     ALLOWED_ORIGINS=http://localhost:8501
     ```

3. **Enable Actions:**
   - Go to "Actions" tab in your repo
   - The workflow will run automatically every hour
   - You can also trigger it manually

4. **View Results:**
   - Check "Actions" tab to see pipeline runs
   - Download database artifact to see collected data

**Note:** Database is stored as artifact and persists between runs.

---

### Option B: Local Scheduler (For Development)

**Run pipelines automatically on your local machine:**

```bash
# Install dependencies
pip install -r requirements.txt

# Run scheduler (runs every hour)
python -m src.pipelines.scheduler --daemon --interval 1

# Or run once
python -m src.pipelines.scheduler --once
```

---

### Option C: Deploy to Cloud (For Dashboard)

**To host your dashboard online, use one of these:**

1. **Render.com** (Easiest, Free tier available)
   - See `DEPLOYMENT.md` for full instructions
   - Deploys API + Dashboard + Scheduler automatically

2. **Railway.app** (Simple, $5/month credit)
   - One-click deployment from GitHub
   - Includes database

3. **VPS** (Full control)
   - Set up cron job to run scheduler
   - Host API and dashboard with nginx

---

## 📋 How It Works

### The Scheduler (`scheduler.py`)

Runs this sequence every hour:
1. **Collect** - Fetches news and Reddit posts
2. **Score** - Analyzes sentiment using NLP
3. **Aggregate Hourly** - Creates hourly sentiment indices
4. **Aggregate Daily** - Creates daily sentiment indices

### GitHub Actions Workflow

- Runs automatically every hour (`0 * * * *`)
- Can be triggered manually
- Saves database as artifact
- Completely free for public repos

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
DB_URL=sqlite:///btc_sentiment.db
NEWS_FEEDS=https://cointelegraph.com/rss,https://decrypt.co/feed
REDDIT_FEEDS=bitcoin,cryptocurrency
COINGECKO_BASE=https://api.coingecko.com/api/v3
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:8000
```

### Scheduler Options

```bash
# Run once and exit
python -m src.pipelines.scheduler --once

# Run as daemon (continuous)
python -m src.pipelines.scheduler --daemon --interval 1

# Custom interval (every 2 hours)
python -m src.pipelines.scheduler --daemon --interval 2
```

---

## 📊 Monitoring

### Check Pipeline Status

**GitHub Actions:**
- Go to "Actions" tab
- See run history and logs
- Download database artifacts

**Local:**
- Check terminal output
- View logs in console
- Check database directly:
  ```bash
  sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM raw_items;"
  ```

### Verify Data Collection

```bash
# Check raw items
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM raw_items;"

# Check scored items
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM scored_items;"

# Check sentiment indices
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM sentiment_indices;"
```

---

## 🎯 Next Steps

1. **Set up GitHub Actions** (if using GitHub)
   - Add secrets
   - Push code
   - Enable Actions

2. **Deploy Dashboard** (optional)
   - Choose platform (Render/Railway/VPS)
   - Follow `DEPLOYMENT.md` guide
   - Point dashboard to your API

3. **Monitor**
   - Check Actions tab
   - Verify data collection
   - Test dashboard

---

## ❓ FAQ

**Q: Can I use GitHub Pages?**  
A: No, GitHub Pages only hosts static sites. Use GitHub Actions for pipelines and Render/Railway for dashboard.

**Q: Is GitHub Actions free?**  
A: Yes, for public repositories. 2000 minutes/month for free.

**Q: How often do pipelines run?**  
A: Every hour by default. Can be customized in workflow file.

**Q: Where is the database stored?**  
A: In GitHub Actions, it's stored as an artifact. For persistent storage, use cloud database (PostgreSQL).

**Q: Can I run this locally?**  
A: Yes! Use `python -m src.pipelines.scheduler --daemon`

---

## 📚 More Information

- **Full deployment guide:** See `DEPLOYMENT.md`
- **How sentiment index works:** See `SENTIMENT_INDEX_EXPLAINED.md`
- **Project README:** See `README.md`

---

**Ready to go!** Push to GitHub and enable Actions to start automated data collection! 🚀

