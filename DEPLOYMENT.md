# Deployment Guide for BTC Sentiment Analysis

## 🎯 Current Setup

Your GitHub Actions pipeline already runs automatically every hour to:
- ✅ Collect new data (RSS feeds, Reddit, BTC price)
- ✅ Score sentiment with FinBERT
- ✅ Aggregate daily/hourly indices  
- ✅ Clean up old data (60-day retention)
- ✅ Save database as artifact for next run

**The data pipeline is fully automated!** Now you just need to deploy the frontend/backend to serve the data.

---

## 🚀 Recommended Deployment (Free Tier)

### Architecture
```
GitHub Actions (hourly)
    ↓ generates database
    ↓
Railway/Render Backend (downloads DB artifact)
    ↑ API calls
    ↑
Vercel Frontend (free, auto-deploy)
```

### 1. Deploy Frontend to Vercel (Free)

**Perfect for Next.js apps with automatic deployments**

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel --prod
```

**Or via Vercel Dashboard:**
1. Go to https://vercel.com/new
2. Import your GitHub repo (`JTRON780/BTC`)
3. Set **Root Directory:** `frontend`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app` (add after backend setup)
5. Click **Deploy**

**Result:** Frontend auto-deploys on every git push to main!

---

### 2. Deploy Backend to Railway (Free 500 hrs/month)

**Perfect for Python APIs with persistent storage**

1. **Create Railway account** at https://railway.app

2. **New Project** → **Deploy from GitHub repo**

3. **Select** `JTRON780/BTC`

4. **Settings:**
   - **Start Command:**
     ```bash
     python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
     ```
   
   - **Environment Variables:**
     ```
     DB_URL=sqlite:///data/btc_sentiment.db
     ALLOWED_ORIGINS=https://your-vercel-app.vercel.app
     ```

5. **Add Persistent Storage:**
   - Railway → **Variables** → **New Volume**
   - **Mount Path:** `/data`
   - This keeps your database between deployments!

6. **Add Database Sync (Optional):**
   
   Create `railway-start.sh` in project root:
   ```bash
   #!/bin/bash
   # Download latest database from GitHub Actions
   mkdir -p /data
   
   # Use GitHub API to get latest artifact (requires GITHUB_TOKEN)
   if [ ! -z "$GITHUB_TOKEN" ]; then
     echo "Downloading latest database from GitHub Actions..."
     curl -L \
       -H "Accept: application/vnd.github+json" \
       -H "Authorization: Bearer $GITHUB_TOKEN" \
       "https://api.github.com/repos/JTRON780/BTC/actions/artifacts" \
       | jq -r '.artifacts[] | select(.name=="database") | .archive_download_url' | head -1 \
       | xargs curl -L -H "Authorization: Bearer $GITHUB_TOKEN" -o /tmp/database.zip
     
     unzip -o /tmp/database.zip -d /data
     rm /tmp/database.zip
   fi
   
   # Start backend
   python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
   ```
   
   Update Railway **Start Command:**
   ```bash
   chmod +x railway-start.sh && ./railway-start.sh
   ```
   
   Add to Railway **Environment Variables:**
   ```
   GITHUB_TOKEN=${{ your GitHub personal access token }}
   ```

7. **Get your Railway URL** (e.g., `https://btc-production.up.railway.app`)

---

### 3. Connect Frontend to Backend

Update Vercel environment variable:
- `NEXT_PUBLIC_API_URL` = `https://your-backend.railway.app`

Update Railway CORS:
- `ALLOWED_ORIGINS` = `https://your-frontend.vercel.app,http://localhost:3000`

**Done!** Your app is live and auto-updates hourly! 🎉

---

## 🔄 Alternative: Render.com (Free with limitations)

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

