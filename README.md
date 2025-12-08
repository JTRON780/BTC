# BTC Sentiment Analysis
Everything Bitcoin - Real-time sentiment analysis and dashboard

## 🚀 Quick Start

### Option 1: Local Development (Recommended)

**Backend (FastAPI):**
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API server
python -m uvicorn src.api.main:app --reload
```

**Frontend (Next.js):**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Access the services:
- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Production Build

**Backend:**
```bash
# Activate environment
source .venv/bin/activate

# Run with production server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend

# Build for production
npm run build

# Start production server
npm start
```

### Option 3: Automated Data Pipeline

**Run pipelines automatically with GitHub Actions:**

```bash
# Manual pipeline execution
python -m src.pipelines.collect    # Fetch news/Reddit/price data
python -m src.pipelines.score      # Run FinBERT sentiment analysis
python -m src.pipelines.aggregate  # Generate daily/hourly indices
python -m src.pipelines.cleanup    # Clean old data (60-day retention)
```

**GitHub Actions:** Pipelines run automatically every hour via `.github/workflows/pipeline.yml`

## 📦 What's Inside

### Backend (FastAPI)
- `/api/v1/sentiment/` - Get sentiment index data (daily/hourly)
- `/api/v1/drivers/` - Get top sentiment drivers (positive/negative articles)
- `/api/v1/health` - Health check endpoint
- Auto-generated OpenAPI docs at `/docs`
- **Sentiment Engine**: FinBERT model for financial sentiment analysis
- **Weighted Aggregation**: News sources (1.2x) + Reddit (1.0x)
- **EWMA Smoothing**: Exponential weighted moving average (α=0.2)

### Frontend (Next.js 14)
- **Modern React UI** with TypeScript + Tailwind CSS
- **Real-time KPI Cards**: Current Sentiment, Raw Sentiment, 24h/7d Changes
### Data Pipeline
- **Collection**: RSS feeds (Cointelegraph, Decrypt) + Reddit (r/bitcoin, r/cryptocurrency)
- **Bitcoin Filtering**: Keyword-based filtering for BTC-specific content
- **Sentiment Scoring**: FinBERT model (ProsusAI/finbert)
- **Aggregation**: Weighted average + EWMA smoothing
- **Retention**: 60-day rolling window for raw data, indefinite for indices
- **Automation**: GitHub Actions hourly cron job

### Testing
```bash
# Run all tests
pytest src/tests/ -v

# Run specific test suite
pytest src/tests/test_api.py -v
pytest src/tests/test_sentiment.py -v
pytest src/tests/test_aggregate.py -v
```

## 🤖 Data Pipeline

### Manual Execution
```bash
# Activate environment
source .venv/bin/activate

# Run full pipeline
python -m src.pipelines.collect      # Fetch data (news, Reddit, prices)
python -m src.pipelines.score        # Score sentiment with FinBERT
python -m src.pipelines.aggregate    # Compute daily/hourly indices
python -m src.pipelines.cleanup      # Remove data older than 60 days

# Backfill historical data
python -m src.pipelines.backfill --days 90           # Price history
python -m src.pipelines.historical_backfill --days 30  # Synthetic content
```

## 📁 Project Structure

```
BTC/
├── frontend/                   # Next.js 14 frontend
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Main dashboard page
│   ├── components/
│   │   ├── kpi-card.tsx       # Metric cards
│   │   ├── sentiment-chart.tsx # Recharts line chart
│   │   └── top-drivers.tsx    # Article lists
│   ├── lib/
│   │   ├── api.ts             # API client
│   │   └── utils.ts           # Utility functions
│   ├── .env.local             # Environment variables
│   └── package.json           # Dependencies
├── src/
│   ├── api/                   # FastAPI backend
│   │   ├── main.py            # App entry point
│   │   ├── routes/            # API endpoints
│   │   │   ├── index.py       # Sentiment index endpoint
│   │   │   ├── top_drivers.py # Top drivers endpoint
│   │   │   └── health.py      # Health check
│   │   └── schemas/           # Pydantic models
│   ├── nlp/                   # NLP processing
│   │   ├── models.py          # FinBERT wrapper
│   │   └── preprocess.py      # Text cleaning
│   ├── pipelines/             # Data pipelines
│   │   ├── collect.py         # Data collection
│   │   ├── score.py           # Sentiment scoring
│   │   ├── aggregate.py       # Index aggregation
│   │   ├── cleanup.py         # Data retention
│   │   └── backfill.py        # Historical data
│   ├── data/                  # Database models
│   │   ├── schemas.py         # SQLAlchemy models
│   │   └── stores.py          # Database operations
│   └── tests/                 # Test suite
│       ├── test_api.py        # API tests
│       ├── test_sentiment.py  # NLP tests
│       └── test_aggregate.py  # Aggregation tests
├── .github/workflows/
│   └── pipeline.yml           # Automated pipeline
├── requirements.txt           # Python dependencies
└── pytest.ini                 # Pytest configuration
``` ├── pipelines/        # Data pipelines
│   └── tests/            # Test suite
│       ├── test_sentiment.py   # 21 NLP tests
│       ├── test_aggregate.py   # 22 aggregation tests
│       └── test_api.py         # 20 E2E API tests
├── Dockerfile            # Multi-stage build
├── docker-compose.yml    # Service orchestration
├── deploy.sh             # Deployment helper script
├── requirements.txt      # Python dependencies
└── pytest.ini           # Pytest configuration

```

## 🧪 Development

### Configuration

## 📊 Architecture

```
┌──────────────────────────────────────────────────────┐
│ Next.js Frontend (Port 3000)                        │
│  - TypeScript + Tailwind CSS                        │
│  - Recharts visualization                           │
│  - Server-side rendering                            │
│  - Real-time data fetching                          │
└────────────┬─────────────────────────────────────────┘
             │ HTTP/fetch API
             ▼
┌──────────────────────────────────────────────────────┐
│ FastAPI Backend (Port 8000)                         │
│  - /api/v1/sentiment/?granularity=daily&days=30     │
│  - /api/v1/drivers/?date=YYYY-MM-DD                 │
│  - /api/v1/health                                   │
│  - CORS Enabled (localhost:3000)                    │
└────────────┬─────────────────────────────────────────┘
             │ SQLAlchemy ORM
             ▼
┌──────────────────────────────────────────────────────┐
│ SQLite Database (data/sentiment.db)                 │
│  - raw_items: RSS/Reddit posts                      │
│  - scored_items: FinBERT sentiment scores           │
│  - sentiment_indices: Daily/hourly aggregations     │
│  - prices: BTC price snapshots                      │
└──────────────────────────────────────────────────────┘
             ▲
             │
┌──────────────────────────────────────────────────────┐
│ Data Pipeline (GitHub Actions Hourly)              │
│  1. collect.py → Fetch RSS + Reddit + Price         │
│  2. score.py → FinBERT sentiment analysis           │
│  3. aggregate.py → Weighted avg + EWMA smoothing    │
│  4. cleanup.py → 60-day retention policy            │
└──────────────────────────────────────────────────────┘
```

## 🧮 Sentiment Calculation

1. **Scoring**: FinBERT model returns `{neg, neu, pos}` probabilities
## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **Next.js** - React framework for production
- **FinBERT** (ProsusAI/finbert) - Financial sentiment model
- **Recharts** - Composable charting library
- **Tailwind CSS** - Utility-first CSS framework
- **Pytest** - Testing frameworkeight)`

3. **EWMA Smoothing** (α=0.2):
   - Formula: `smoothed = 0.2 × raw + 0.8 × previous_smoothed`
   - Reduces noise while preserving trends
# Type checking
mypy src/
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│ Streamlit Dashboard (Port 8501)                │
│  - KPI Cards                                    │
│  - Plotly Charts                                │
│  - Gauge Visualization                          │
│  - Top Drivers Display                          │
└────────────┬────────────────────────────────────┘
             │ HTTP Requests
             ▼
┌─────────────────────────────────────────────────┐
│ FastAPI Backend (Port 8000)                    │
│  - /api/v1/sentiment/                           │
│  - /api/v1/drivers/                             │
│  - /api/v1/health                               │
│  - CORS Enabled                                 │
└────────────┬────────────────────────────────────┘
             │ SQLAlchemy
             ▼
┌─────────────────────────────────────────────────┐
│ SQLite Database                                │
│  - Sentiment indices                            │
│  - Post data                                    │
│  - Aggregations                                 │
└─────────────────────────────────────────────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest src/tests/`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FastAPI for the modern API framework
- Streamlit for the intuitive dashboard framework
- Plotly for interactive visualizations
- Pytest for comprehensive testing capabilities

