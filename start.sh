#!/bin/bash
set -e

echo "🚀 Starting BTC Sentiment API..."

# Create data directory if it doesn't exist
mkdir -p /data

# Download latest database from GitHub Releases (updated hourly by Actions)
if [ ! -f /data/btc_sentiment.db ]; then
    echo "📥 No database found, downloading latest from GitHub..."
    
    # Get latest release with database
    LATEST_DB_URL=$(curl -s "https://api.github.com/repos/${GITHUB_REPO:-JTRON780/BTC}/releases" | \
        grep -o 'https://github.com/.*/releases/download/.*/btc_sentiment.db' | head -1)
    
    if [ ! -z "$LATEST_DB_URL" ]; then
        echo "📦 Downloading: $LATEST_DB_URL"
        curl -L "$LATEST_DB_URL" -o /data/btc_sentiment.db
        echo "✅ Database downloaded successfully"
    else
        echo "⚠️  No database release found on GitHub"
        echo "   The database will be empty until GitHub Actions runs"
        echo "   (runs automatically every hour)"
    fi
else
    echo "✅ Database already exists at /data/btc_sentiment.db"
fi

# Optional: Update database from GitHub if it's older than 2 hours
DB_AGE_SECONDS=$(( $(date +%s) - $(stat -c %Y /data/btc_sentiment.db 2>/dev/null || echo 0) ))
if [ $DB_AGE_SECONDS -gt 7200 ]; then
    echo "🔄 Database is older than 2 hours, checking for updates..."
    LATEST_DB_URL=$(curl -s "https://api.github.com/repos/${GITHUB_REPO:-JTRON780/BTC}/releases" | \
        grep -o 'https://github.com/.*/releases/download/.*/btc_sentiment.db' | head -1)
    
    if [ ! -z "$LATEST_DB_URL" ]; then
        echo "📦 Downloading updated database..."
        curl -L "$LATEST_DB_URL" -o /data/btc_sentiment.db.new && \
        mv /data/btc_sentiment.db.new /data/btc_sentiment.db
        echo "✅ Database updated successfully"
    fi
fi

echo "🗄️  Database ready at /data/btc_sentiment.db"
echo "🌐 Starting Uvicorn server on port ${PORT:-8000}..."

# Start the API server
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
