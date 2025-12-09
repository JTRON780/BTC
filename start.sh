#!/bin/bash
set -e

echo "🚀 Starting BTC Sentiment API..."

# Create data directory if it doesn't exist
mkdir -p /data

echo "📥 Downloading latest database from GitHub Releases..."

# Get latest release with database (public, no auth needed)
LATEST_DB_URL=$(curl -s "https://api.github.com/repos/JTRON780/BTC/releases" | \
    grep -o 'https://github.com/JTRON780/BTC/releases/download/[^"]*btc_sentiment.db' | head -1)

if [ ! -z "$LATEST_DB_URL" ]; then
    echo "📦 Downloading: $LATEST_DB_URL"
    curl -L "$LATEST_DB_URL" -o /data/btc_sentiment.db
    echo "✅ Database downloaded successfully"
    ls -lh /data/btc_sentiment.db
else
    echo "⚠️  No database release found on GitHub"
    echo "   Starting with empty database"
    echo "   GitHub Actions will populate it hourly"
fi

echo "🗄️  Database ready at /data/btc_sentiment.db"
echo "🌐 Starting Uvicorn server on port ${PORT:-8000}..."

# Start the API server
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
