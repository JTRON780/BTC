# Docker Deployment Guide

## Quick Start

### 1. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode (background)
docker-compose up -d --build
```

### 2. Access Services

- **FastAPI Backend**: http://localhost:8000
  - API Documentation: http://localhost:8000/docs
  - Health Check: http://localhost:8000/api/v1/health
  - Sentiment Index: http://localhost:8000/api/v1/sentiment/
  - Top Drivers: http://localhost:8000/api/v1/drivers/

- **Streamlit Dashboard**: http://localhost:8501

### 3. Stop Services

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes data)
docker-compose down -v
```

## Individual Service Management

### Run API Only

```bash
docker-compose up api
```

### Run Dashboard Only

```bash
# Requires API to be running
docker-compose up app
```

### View Logs

```bash
# All services
docker-compose logs -f

# API only
docker-compose logs -f api

# Dashboard only
docker-compose logs -f app
```

## Advanced Usage

### Build Individual Images

```bash
# Build API image
docker build -t btc-sentiment-api --build-arg MODE=api .

# Build Dashboard image
docker build -t btc-sentiment-app --build-arg MODE=app .
```

### Run Individual Containers

```bash
# Run API
docker run -p 8000:8000 \
  -v btc-sentiment-data:/app/data \
  --env-file .env \
  btc-sentiment-api

# Run Dashboard
docker run -p 8501:8501 \
  -v btc-sentiment-data:/app/data \
  --env-file .env \
  -e API_BASE_URL=http://api:8000 \
  btc-sentiment-app
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Required variables:
- Database configuration
- API keys (if applicable)
- Other service-specific settings

### Persistent Data

The SQLite database is stored in a named Docker volume `btc-sentiment-data`, which persists across container restarts.

**View volume details:**
```bash
docker volume inspect btc-sentiment-data
```

**Backup volume:**
```bash
docker run --rm -v btc-sentiment-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/btc-data-backup.tar.gz -C /data .
```

**Restore volume:**
```bash
docker run --rm -v btc-sentiment-data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/btc-data-backup.tar.gz -C /data
```

## Troubleshooting

### Check Service Health

```bash
# API health check
curl http://localhost:8000/api/v1/health

# Check container status
docker-compose ps
```

### Rebuild from Scratch

```bash
# Remove all containers, images, and volumes
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### View Container Details

```bash
# List running containers
docker ps

# Execute commands inside container
docker-compose exec api bash
docker-compose exec app bash
```

## Production Deployment

For production deployment, consider:

1. **Use a production WSGI server** (already using uvicorn)
2. **Add nginx reverse proxy** for SSL/TLS
3. **Use managed database** instead of SQLite
4. **Enable monitoring** (Prometheus, Grafana)
5. **Configure logging** (centralized logging)
6. **Set resource limits** in docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│ Docker Compose Network                          │
│                                                 │
│  ┌──────────────┐         ┌──────────────┐     │
│  │   API        │         │   Dashboard  │     │
│  │  (FastAPI)   │◄────────│  (Streamlit) │     │
│  │  Port: 8000  │         │  Port: 8501  │     │
│  └──────┬───────┘         └──────────────┘     │
│         │                                       │
│         │ Shared Volume: btc-sentiment-data    │
│         ▼                                       │
│  ┌──────────────┐                               │
│  │   SQLite DB  │                               │
│  │  /app/data   │                               │
│  └──────────────┘                               │
└─────────────────────────────────────────────────┘
```

## Dockerfile Details

- **Multi-stage build**: Separates dependency installation from runtime
- **Base image**: python:3.11-slim (minimal size)
- **MODE argument**: Switches between API and Dashboard modes
- **Optimized layers**: Cached dependency installation
- **Health checks**: Built-in API health monitoring
