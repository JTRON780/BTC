# BTC Market Outlook

This is a serverless, automated Bitcoin sentiment dashboard that tracks market sentiment using NLP (FinBERT) on news and Reddit posts. It runs entirely on GitHub infrastructure (Actions for backend, Pages for API) and Vercel (Frontend).

**Live Dashboard**: [btc-delta-one.vercel.app](https://btc-delta-one.vercel.app)  
**API**: [jtron780.github.io/BTC](https://jtron780.github.io/BTC)

## Tech Stack

**Backend**:
- Python 3.x with FastAPI
- FinBERT for sentiment analysis (via Hugging Face Transformers)
- SQLAlchemy ORM with SQLite
- Feedparser for RSS feeds
- PRAW for Reddit API

**Frontend**:
- Next.js 16 with React 19
- TypeScript & Tailwind CSS
- Recharts for data visualization
- Lucide React for icons

**Infrastructure**:
- GitHub Actions for hourly automation
- GitHub Pages for static JSON API
- Vercel for frontend hosting

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/JTRON780/BTC.git
cd BTC
```

### 2. Set Up Python Backend
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
# Copy example env
cp .env.example .env

# Add your credentials:
# - REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET
# - COINGECKO_API_KEY (optional)
```

### 4. Run Data Pipeline
```bash
# Collect data and analyze sentiment
python -m src.pipelines.collect

# Export to JSON for GitHub Pages
python -m src.pipelines.export_json
```

### 5. Run Frontend (Local Development)
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

## Project Structure

```
├── src/
│   ├── api/              # FastAPI routes
│   ├── ingest/           # Data collectors (news, reddit, price)
│   ├── nlp/              # Sentiment analysis (FinBERT)
│   ├── pipelines/        # Orchestration & exports
│   ├── data/             # Database schemas & utilities
│   ├── core/             # Config & logging
│   └── tests/            # Unit tests
├── frontend/             # Next.js dashboard
├── api-output/           # Generated static JSON files
└── .github/workflows/    # GitHub Actions automation
```

## Key Pipelines

**`collect`** - Hourly data collection
- Fetches RSS feeds, Reddit posts, Bitcoin price
- Runs sentiment analysis on all items
- Aggregates daily/hourly indices
- Stores in SQLite database

**`export_json`** - Static API generation
- Exports 30 days of daily sentiment
- Exports 7 days of hourly sentiment
- Exports top drivers (positive/negative posts) by day
- Creates index.json with endpoint documentation

## API Endpoints

All endpoints return JSON and are served via GitHub Pages:

```
GET /index.json                 # API documentation
GET /sentiment_daily.json       # Daily sentiment (30 days)
GET /sentiment_hourly.json      # Hourly sentiment (7 days)
GET /price.json                 # Current BTC price
GET /drivers/YYYY-MM-DD.json    # Top posts for specific day
```

### Example: Daily Sentiment
```json
{
  "granularity": "daily",
  "data": [
    {
      "ts": "2025-12-01T00:00:00",
      "raw": 0.62,
      "smoothed": 0.61,
      "n_posts": 245
    }
  ]
}
```

## Data Sources

| Source | Type | Frequency | Count |
|--------|------|-----------|-------|
| Cointelegraph, Decrypt, CoinDesk, Bitcoin Magazine | News | Hourly | 11 feeds |
| r/cryptocurrency, r/bitcoin, r/BitcoinBeginners | Reddit | Hourly | 8 subreddits |
| CoinGecko | Price | Hourly | 1 API |

**Bitcoin Filtering**: Uses strict keyword matching (`btc`, `satoshi`, `lightning network`, `taproot`, `ordinals`) and negative lookahead patterns to exclude posts primarily about other cryptocurrencies (e.g. ETH, SOL) unless Bitcoin is explicitly discussed.

## NLP Model

- **Primary**: FinBERT (ProsusAI/finbert)
- **Fallback**: DistilBERT
- **Output**: 3-class sentiment (positive/neutral/negative) + polarity score
- **Training**: Financial sentiment classification

## Development

### Running Tests
```bash
pytest src/tests/
```

### Local Database
```bash
# Initialize SQLite database
python -c "from src.data import init_db; init_db('sqlite:///btc_sentiment.db')"

# Inspect data
sqlite3 btc_sentiment.db
```

### Docker
```bash
docker-compose up -d
```

## Deployment

### Frontend (Vercel)
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL environment variable
```

### GitHub Actions Setup
1. Create `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` secrets
2. GitHub Actions runs hourly to collect data & export JSON
3. Deploys JSON to GitHub Pages branch automatically

See `QUICKSTART.md` for detailed setup instructions.

## Configuration

Key environment variables:

```env
DB_URL=sqlite:///btc_sentiment.db
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
COINGECKO_API_KEY=optional
NEXT_PUBLIC_API_URL=https://jtron780.github.io/BTC
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design & data flow
- **[SENTIMENT_INDEX_EXPLAINED.md](SENTIMENT_INDEX_EXPLAINED.md)** - How sentiment is calculated
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

## License

MIT License - see [LICENSE](LICENSE) file

## Author

Created by [JTRON780](https://github.com/JTRON780)

---

**Questions?** Check the documentation or open an issue on GitHub.

