# BTC Sentiment Analysis
Everything Bitcoin - Real-time sentiment analysis and dashboard

## 🚀 Quick Start

### Option 1: Automated Scheduling (New! ⭐)

**Run pipelines automatically with GitHub Actions or local scheduler:**

```bash
# Local scheduler (runs every hour)
python -m src.pipelines.scheduler --daemon --interval 1

# Or run once
python -m src.pipelines.scheduler --once
```

**GitHub Actions:** See `AUTOMATION_SETUP.md` for setup instructions. Pipelines run automatically every hour!

### Option 2: Docker (Recommended for Full Stack)

The easiest way to run the entire stack:

```bash
# Using deployment script
./deploy.sh start

# Or using Docker Compose directly
docker compose up -d
```

Access the services:
- **Dashboard**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 3: Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API
uvicorn src.api.main:app --reload

# Run Dashboard (in separate terminal)
streamlit run src/app/dashboard.py
```

## 📦 What's Inside

### Backend (FastAPI)
- `/api/v1/sentiment/` - Get sentiment index data
- `/api/v1/drivers/` - Get top sentiment drivers
- `/api/v1/health` - Health check endpoint
- Auto-generated OpenAPI docs at `/docs`

### Frontend (Streamlit)
- Real-time KPI cards (Current Index, 24h Change, Volatility)
- Interactive Plotly charts with zoom/pan
- Gauge visualization for sentiment strength
- Top positive/negative drivers display

### Testing
- 63 comprehensive tests (unit + E2E)
- Pytest with custom markers (`@pytest.mark.fast`, `@pytest.mark.e2e`)
- 100% passing test suite

```bash
# Run all tests
pytest src/tests/ --quiet

# Run fast tests only
pytest src/tests/ -m fast
```

## 🤖 Automated Pipeline Scheduling

**New!** Pipelines can now run automatically:
- **GitHub Actions** - Runs every hour (free for public repos)
- **Local Scheduler** - Run on your machine with `python -m src.pipelines.scheduler --daemon`
- **Cloud Deployment** - Deploy to Render/Railway for continuous operation

See [AUTOMATION_SETUP.md](AUTOMATION_SETUP.md) for quick start guide.  
See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment options.

## 🐋 Docker Deployment

See [DOCKER.md](DOCKER.md) for comprehensive Docker deployment guide.

**Quick Commands:**
```bash
./deploy.sh build      # Build images
./deploy.sh start      # Start services
./deploy.sh stop       # Stop services
./deploy.sh logs       # View logs
./deploy.sh status     # Check health
./deploy.sh clean      # Remove everything
```

## 📁 Project Structure

```
BTC/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # App entry point
│   │   ├── routes/       # API endpoints
│   │   └── schemas/      # Pydantic models
│   ├── app/              # Streamlit frontend
│   │   ├── dashboard.py  # Main dashboard
│   │   └── __init__.py   # Launch helpers
│   ├── nlp/              # NLP processing
│   ├── pipelines/        # Data pipelines
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

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Running Tests

```bash
# All tests
pytest src/tests/ -v

# Specific test file
pytest src/tests/test_sentiment.py -v

# With coverage
pytest src/tests/ --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint
flake8 src/

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

