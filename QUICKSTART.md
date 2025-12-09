# Quick Start - GitHub Pages API

## Setup (One-time)

### 1. Enable GitHub Pages
```bash
# In repository settings
Settings → Pages → Source: gh-pages branch
```

### 2. Configure Vercel
```bash
./setup-vercel-env.sh
# Sets NEXT_PUBLIC_API_URL=https://jtron780.github.io/BTC
```

### 3. Deploy Frontend
```bash
cd frontend
vercel --prod
```

## How It Works

```
GitHub Actions (hourly)
  ↓
Collect data → Analyze sentiment → Export JSON
  ↓
Deploy to GitHub Pages
  ↓
Vercel frontend fetches JSON
```

## API Endpoints

Base: `https://jtron780.github.io/BTC`

- `/index.json` - API docs
- `/sentiment_daily.json` - Daily sentiment (30 days)
- `/sentiment_hourly.json` - Hourly sentiment (7 days)
- `/price.json` - Current BTC price with 24h change
- `/drivers/YYYY-MM-DD.json` - Top posts for specific day

## Testing

```bash
# Check API is live
curl https://jtron780.github.io/BTC/index.json

# Check latest sentiment
curl https://jtron780.github.io/BTC/sentiment_daily.json

# Check current price
curl https://jtron780.github.io/BTC/price.json
```

## Monitoring

- **GitHub Actions**: https://github.com/JTRON780/BTC/actions
- **GitHub Pages**: Settings → Pages
- **Vercel**: https://vercel.com/dashboard

## Troubleshooting

### API returns 404
- Check GitHub Pages is enabled
- Verify `gh-pages` branch exists
- Wait 10 minutes after Actions completes

### Frontend shows loading forever
- Check browser console for errors
- Verify `NEXT_PUBLIC_API_URL` in Vercel settings
- Test API endpoint directly with curl

### Data is outdated
- Check GitHub Actions last run time
- Verify workflow completed successfully
- GitHub Actions runs hourly on the hour

## Manual Trigger

```bash
# Trigger data collection now
gh workflow run pipeline.yml

# Check status
gh workflow view pipeline.yml
```

## Key Files

- `.github/workflows/pipeline.yml` - Automation
- `src/pipelines/export_json.py` - JSON export
- `frontend/lib/api.ts` - API client
- `ARCHITECTURE.md` - Full documentation
