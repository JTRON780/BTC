# Deployment Guide for BTC Sentiment Analysis

## ⚠️ Important: GitHub Pages Limitation

**GitHub Pages cannot run Python applications or scheduled tasks.** It only hosts static HTML/CSS/JS files.

However, we can use **GitHub Actions** to run the pipelines automatically, and deploy the dashboard to alternative platforms.

---

## 🚀 Deployment Options

### Option 1: GitHub Actions (Recommended for Automation) ✅

**Best for:** Automated data collection and processing

**What it does:**
- Runs pipelines on a schedule (every hour)
- Stores database as artifact
- Completely free for public repositories

**Setup:**

1. **Add GitHub Secrets:**
   Go to: `Settings > Secrets and variables > Actions > New repository secret`
   
   Add these secrets:
   ```
   NEWS_FEEDS=https://cointelegraph.com/rss,https://decrypt.co/feed
   REDDIT_FEEDS=bitcoin,cryptocurrency
   COINGECKO_BASE=https://api.coingecko.com/api/v3
   ALLOWED_ORIGINS=https://your-domain.com
   ```

2. **The workflow is already configured** in `.github/workflows/pipeline.yml`
   - Runs every hour automatically
   - Can be triggered manually via "Actions" tab

3. **View results:**
   - Check "Actions" tab to see pipeline runs
   - Database is saved as artifact (downloadable)

**Limitations:**
- Database is ephemeral (resets if artifact expires)
- No persistent storage between runs
- Cannot host dashboard directly

---

### Option 2: Render.com (Recommended for Full Deployment) 🌟

**Best for:** Complete deployment with dashboard + API + scheduled tasks

**Free tier includes:**
- Web services (API + Dashboard)
- Background workers (scheduled pipelines)
- PostgreSQL database (persistent)
- Free SSL certificates

**Setup:**

1. **Create account:** https://render.com

2. **Deploy API:**
   - New > Web Service
   - Connect GitHub repo
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables from `.env`

3. **Deploy Dashboard:**
   - New > Web Service
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run src/app/dashboard.py --server.port $PORT --server.address 0.0.0.0`
   - Set `API_BASE_URL` env var to your API URL

4. **Deploy Background Worker (Scheduler):**
   - New > Background Worker
   - Build command: `pip install -r requirements.txt`
   - Start command: `python -m src.pipelines.scheduler --daemon --interval 1`
   - Runs pipelines every hour automatically

5. **Database:**
   - Use Render's PostgreSQL (free tier)
   - Update `DB_URL` in environment variables

**Cost:** Free tier is generous, paid plans start at $7/month

---

### Option 3: Railway.app 🚂

**Best for:** Simple deployment with minimal configuration

**Free tier includes:**
- $5/month credit (usually enough for small apps)
- PostgreSQL database
- Automatic deployments from GitHub

**Setup:**

1. **Create account:** https://railway.app

2. **Deploy from GitHub:**
   - New Project > Deploy from GitHub
   - Select repository
   - Railway auto-detects services

3. **Add services:**
   - API service (FastAPI)
   - Dashboard service (Streamlit)
   - Worker service (scheduler)

4. **Add PostgreSQL:**
   - New > Database > PostgreSQL
   - Update `DB_URL` environment variable

**Cost:** Free tier with $5 credit, then pay-as-you-go

---

### Option 4: Heroku 🟣

**Best for:** Traditional PaaS deployment

**Setup:**

1. **Install Heroku CLI**

2. **Create apps:**
   ```bash
   heroku create btc-sentiment-api
   heroku create btc-sentiment-dashboard
   heroku create btc-sentiment-worker
   ```

3. **Add PostgreSQL:**
   ```bash
   heroku addons:create heroku-postgresql:mini -a btc-sentiment-api
   ```

4. **Deploy:**
   ```bash
   git push heroku main
   ```

5. **Set up scheduler:**
   - Use Heroku Scheduler addon (free tier available)
   - Run: `python -m src.pipelines.scheduler --once`

**Cost:** Free tier discontinued, paid plans start at $7/month

---

### Option 5: VPS (DigitalOcean, Linode, etc.) 💻

**Best for:** Full control and custom setup

**Setup:**

1. **Provision VPS** (Ubuntu 22.04 recommended)

2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3-pip nginx
   ```

3. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/BTC.git
   cd BTC
   pip install -r requirements.txt
   ```

4. **Set up systemd services:**
   - API service
   - Dashboard service
   - Scheduler service

5. **Configure cron for scheduler:**
   ```bash
   # Edit crontab
   crontab -e
   
   # Add: Run pipeline every hour
   0 * * * * cd /path/to/BTC && python -m src.pipelines.scheduler --once
   ```

6. **Set up Nginx reverse proxy** for API and Dashboard

**Cost:** $5-10/month for basic VPS

---

## 📋 Quick Start: Local Scheduler

For local development or testing:

```bash
# Install dependencies
pip install -r requirements.txt

# Run scheduler as daemon (runs every hour)
python -m src.pipelines.scheduler --daemon --interval 1

# Or run once
python -m src.pipelines.scheduler --once
```

---

## 🔧 Environment Variables

Create `.env` file with:

```bash
DB_URL=sqlite:///btc_sentiment.db
NEWS_FEEDS=https://cointelegraph.com/rss,https://decrypt.co/feed
REDDIT_FEEDS=bitcoin,cryptocurrency
COINGECKO_BASE=https://api.coingecko.com/api/v3
ALLOWED_ORIGINS=http://localhost:8501,http://localhost:8000
```

For production with PostgreSQL:
```bash
DB_URL=postgresql://user:password@host:5432/dbname
```

---

## 🎯 Recommended Setup

**For automated data collection:**
- ✅ GitHub Actions (runs pipelines hourly)
- ✅ Render.com or Railway (hosts dashboard + API)

**For local development:**
- ✅ Run scheduler locally: `python -m src.pipelines.scheduler --daemon`

**For production:**
- ✅ Render.com or Railway (easiest)
- ✅ VPS with systemd + cron (most control)

---

## 📊 Monitoring

**Check pipeline status:**
- GitHub Actions: View in "Actions" tab
- Render/Railway: View in dashboard logs
- Local: Check logs in terminal

**Database status:**
```bash
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM raw_items;"
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM scored_items;"
sqlite3 btc_sentiment.db "SELECT COUNT(*) FROM sentiment_indices;"
```

---

## 🆘 Troubleshooting

**Pipeline not running:**
- Check environment variables are set
- Verify database connection
- Check logs for errors

**No data in dashboard:**
- Ensure pipelines have run at least once
- Check database has data
- Verify API is running and accessible

**GitHub Actions failing:**
- Check secrets are set correctly
- Verify workflow file syntax
- Check Actions logs for errors

---

## 📝 Next Steps

1. **Choose deployment option** based on your needs
2. **Set up GitHub Actions** for automated pipelines
3. **Deploy dashboard** to Render/Railway
4. **Monitor** pipeline runs and data collection
5. **Customize** feeds and settings as needed

---

**Questions?** Check the main README.md or open an issue on GitHub.

