# BTC Sentiment Analysis - Architecture

## Overview

This project analyzes Bitcoin sentiment from news and social media, displaying insights through a web dashboard. The architecture is fully serverless, using GitHub Actions for automation and GitHub Pages for the API.

## System Components

### 1. Data Collection (GitHub Actions)
- **Schedule**: Runs hourly via GitHub Actions cron (`0 * * * *`)
- **Sources**:
  - 11 RSS news feeds (Cointelegraph, Decrypt, CoinDesk, Bitcoin Magazine, etc.)
  - 8 Reddit subreddits with Bitcoin keyword filtering
  - CoinGecko API for Bitcoin price data
- **Storage**: SQLite database persisted via GitHub Releases

### 2. NLP Analysis
- **Model**: FinBERT (ProsusAI/finbert) for financial sentiment analysis
- **Fallback**: DistilBERT if FinBERT unavailable
- **Output**: 3-class sentiment (positive/neutral/negative) with polarity scores

### 3. Static JSON API (GitHub Pages)
- **Deployment**: GitHub Actions exports data to JSON files
- **Action**: `peaceiris/actions-gh-pages@v3` deploys to `gh-pages` branch
- **URL**: `https://jtron780.github.io/BTC/`
- **Update Frequency**: Hourly (after data collection completes)

### 4. Frontend Dashboard (Vercel)
- **Framework**: Next.js with React
- **Hosting**: Vercel
- **API Client**: Fetches JSON from GitHub Pages
- **URL**: Configured via Vercel environment variable `NEXT_PUBLIC_API_URL`

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Hourly)                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Download database from latest release                   │
│ 2. Collect news (RSS feeds)                                │
│ 3. Collect social media (Reddit)                           │
│ 4. Fetch Bitcoin price (CoinGecko)                         │
│ 5. Run sentiment analysis (FinBERT)                        │
│ 6. Aggregate sentiment indices                             │
│ 7. Export to JSON files                                    │
│ 8. Upload database to new release                          │
│ 9. Deploy JSON files to GitHub Pages                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Pages (Static)                   │
├─────────────────────────────────────────────────────────────┤
│ /index.json          - API documentation                   │
│ /sentiment_daily.json - Daily sentiment index (30 days)    │
│ /sentiment_hourly.json - Hourly sentiment index (7 days)   │
│ /price.json          - Current BTC price with 24h change   │
│ /drivers/{date}.json - Top positive/negative posts by day  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Frontend (Next.js)                │
├─────────────────────────────────────────────────────────────┤
│ - Fetches JSON from GitHub Pages                           │
│ - Displays KPI cards (price, sentiment)                    │
│ - Renders sentiment chart                                  │
│ - Shows top drivers (positive/negative posts)              │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints (GitHub Pages)

### Base URL
```
https://jtron780.github.io/BTC/
```

### Endpoints

#### `GET /index.json`
API documentation and metadata
```json
{
  "name": "BTC Sentiment Analysis API",
  "version": "1.0",
  "updated": "2025-01-27T10:00:00Z",
  "endpoints": [...]
}
```

#### `GET /sentiment_daily.json`
Daily sentiment indices for last 30 days
```json
{
  "indices": [
    {
      "timestamp": "2025-01-27T00:00:00Z",
      "sentiment": 0.52,
      "polarity": 0.15,
      "total_items": 125
    }
  ]
}
```

#### `GET /sentiment_hourly.json`
Hourly sentiment indices for last 7 days
```json
{
  "indices": [
    {
      "timestamp": "2025-01-27T10:00:00Z",
      "sentiment": 0.54,
      "polarity": 0.18,
      "total_items": 42
    }
  ]
}
```

#### `GET /price.json`
Current Bitcoin price with 24h change
```json
{
  "price": 93736.50,
  "price_change_24h": 3.67,
  "volume_24h": 28500000000,
  "last_updated": "2025-01-27T10:00:00Z"
}
```

#### `GET /drivers/{date}.json`
Top sentiment drivers for specific date (YYYY-MM-DD)
```json
{
  "day": "2025-01-27",
  "positives": [
    {
      "title": "abc123",
      "polarity": 0.95,
      "ts": "2025-01-27T08:00:00Z",
      "source": "cointelegraph"
    }
  ],
  "negatives": [...]
}
```

## Database Schema

### Tables
- `raw_items`: Collected articles/posts before sentiment analysis
- `scored_items`: Analyzed items with sentiment scores
- `sentiment_indices`: Aggregated sentiment by time period
- `price_snapshots`: Historical Bitcoin price data

### Persistence
- Database file: `btc_sentiment.db` (SQLite)
- Storage: GitHub Releases with timestamped tags (`db-YYYYMMDD-HHMMSS`)
- Accumulation: Each run downloads latest, appends new data, uploads updated version

## Configuration

### GitHub Actions Secrets
- `GH_TOKEN`: GitHub token (auto-provided as `${{ github.token }}`)

### Vercel Environment Variables
- `NEXT_PUBLIC_API_URL`: `https://jtron780.github.io/BTC`

### GitHub Pages
- **Source**: Deploy from `gh-pages` branch
- **Enable**: Settings → Pages → Source: `gh-pages`

## Deployment

### Initial Setup
1. Fork/clone repository
2. Enable GitHub Actions
3. Enable GitHub Pages (Settings → Pages → Source: `gh-pages`)
4. Deploy frontend to Vercel:
   ```bash
   cd frontend
   vercel --prod
   ```
5. Set Vercel environment variable:
   ```bash
   ./setup-vercel-env.sh
   ```

### Updates
- **Backend**: Automatic hourly via GitHub Actions
- **Frontend**: Auto-deploy on push to main (Vercel GitHub integration)

### Manual Trigger
```bash
# Trigger GitHub Actions workflow manually
gh workflow run pipeline.yml
```

## Key Features

### Sentiment Index
- Normalized score 0-1 (0 = very negative, 1 = very positive)
- Based on FinBERT polarity scores
- Aggregated by hour or day

### Bitcoin Filtering
Reddit posts filtered by keywords:
- bitcoin, btc, sats, satoshi
- lightning network, taproot, segwit
- halving, mining, hash rate, difficulty

### Data Sources
**News Feeds** (11):
- Cointelegraph, Decrypt, CoinDesk
- Bitcoin Magazine, Reuters, Bloomberg
- Financial Times, The Block, CryptoSlate
- Google News, Yahoo Finance

**Reddit Subreddits** (8):
- r/cryptocurrency, r/bitcoin, r/CryptoMarkets
- r/BitcoinMarkets, r/ethtrader
- r/CryptoCurrencyTrading, r/defi, r/cryptotechnology

## Advantages of This Architecture

1. **No Server Costs**: GitHub Pages and Actions are free for public repos
2. **No Cold Starts**: Static JSON files load instantly
3. **Reliable**: No backend server to crash or timeout
4. **Scalable**: CDN-backed GitHub Pages handles traffic
5. **Simple**: No container orchestration or server management
6. **Transparent**: All code and data processing visible in GitHub Actions logs

## Limitations

- API data updates hourly (not real-time)
- GitHub Actions limited to 2000 minutes/month (public repos unlimited)
- GitHub Pages has 100GB bandwidth soft limit per month
- Database grows over time (monitored via release sizes)

## Monitoring

- **GitHub Actions**: Check workflow runs for failures
- **GitHub Pages**: Monitor deployment success in Pages settings
- **Database Size**: Track release artifact sizes
- **API Availability**: Check `https://jtron780.github.io/BTC/index.json`
