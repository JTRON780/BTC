#!/bin/bash
set -e

echo "🚀 Starting BTC Sentiment API..."
echo ""

# Determine database location based on environment
# Render uses /data for persistent storage, local uses current directory
if [ -w "/data" ]; then
    DB_DIR="/data"
    echo "📁 Using persistent storage: /data"
else
    DB_DIR="/app"
    echo "📁 Using app directory: /app"
fi

mkdir -p "$DB_DIR"
DB_PATH="$DB_DIR/btc_sentiment.db"

echo "📥 Checking for latest database from GitHub Releases..."
echo ""

# Get latest release with database (public, no auth needed)
LATEST_RELEASE=$(curl -s "https://api.github.com/repos/JTRON780/BTC/releases" | \
    grep -A 3 '"tag_name".*"db-' | head -20)

if [ ! -z "$LATEST_RELEASE" ]; then
    LATEST_DB_URL=$(echo "$LATEST_RELEASE" | grep -o 'https://github.com/JTRON780/BTC/releases/download/[^"]*btc_sentiment.db' | head -1)
    
    if [ ! -z "$LATEST_DB_URL" ]; then
        echo "✅ Found database release"
        echo "   URL: $LATEST_DB_URL"
        echo ""
        echo "📦 Downloading database..."
        
        if curl -L -f "$LATEST_DB_URL" -o "$DB_PATH.tmp"; then
            mv "$DB_PATH.tmp" "$DB_PATH"
            echo "✅ Database downloaded successfully"
            echo "   Location: $DB_PATH"
            echo "   Size: $(du -h "$DB_PATH" | cut -f1)"
            
            # Check database contents if sqlite3 is available
            if command -v sqlite3 &> /dev/null; then
                echo ""
                echo "📊 Database contents:"
                sqlite3 "$DB_PATH" "SELECT granularity, COUNT(*) as records FROM sentiment_indices GROUP BY granularity;" 2>/dev/null || echo "   (Unable to query - may be empty)"
            fi
        else
            echo "❌ Failed to download database"
            if [ -f "$DB_PATH" ]; then
                echo "ℹ️  Using existing database"
            else
                echo "⚠️  No database available - will start with empty database"
            fi
        fi
    else
        echo "⚠️  No database file found in releases"
    fi
else
    echo "⚠️  No database releases found on GitHub"
    echo "   GitHub Actions will create releases hourly"
fi

echo ""
echo "🗄️  Database path: $DB_PATH"

# Show final database status
if [ -f "$DB_PATH" ]; then
    echo "✅ Database file exists ($(du -h "$DB_PATH" | cut -f1))"
else
    echo "⚠️  No database file - API will return empty data until GitHub Actions runs"
fi

echo ""
echo "🌐 Starting Uvicorn server on 0.0.0.0:${PORT:-8000}..."
echo ""

# Start the API server
exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
