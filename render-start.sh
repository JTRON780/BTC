#!/bin/bash
# Render startup script - downloads latest database from GitHub Releases
# This runs before starting the API server

set -e

echo "🚀 Starting Render deployment..."
echo ""

# Create data directory if it doesn't exist
mkdir -p /opt/render/project/src/data
cd /opt/render/project/src

DB_PATH="/opt/render/project/src/btc_sentiment.db"

# Check if database already exists
if [ -f "$DB_PATH" ]; then
    echo "📊 Existing database found:"
    ls -lh "$DB_PATH"
    echo ""
fi

# Download latest database from GitHub Releases
echo "🔄 Checking for latest database from GitHub Releases..."

# Get the latest release with database
LATEST_RELEASE=$(curl -s https://api.github.com/repos/JTRON780/BTC/releases | \
    jq -r '[.[] | select(.tag_name | startswith("db-"))] | .[0]')

if [ "$LATEST_RELEASE" != "null" ] && [ -n "$LATEST_RELEASE" ]; then
    RELEASE_TAG=$(echo "$LATEST_RELEASE" | jq -r '.tag_name')
    DB_DOWNLOAD_URL=$(echo "$LATEST_RELEASE" | jq -r '.assets[] | select(.name == "btc_sentiment.db") | .browser_download_url')
    RELEASE_DATE=$(echo "$LATEST_RELEASE" | jq -r '.created_at')
    
    if [ -n "$DB_DOWNLOAD_URL" ] && [ "$DB_DOWNLOAD_URL" != "null" ]; then
        echo "✅ Found database release: $RELEASE_TAG"
        echo "   Created: $RELEASE_DATE"
        echo "   URL: $DB_DOWNLOAD_URL"
        echo ""
        echo "📥 Downloading database..."
        
        # Download with retry logic
        MAX_RETRIES=3
        RETRY_COUNT=0
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if curl -L -f "$DB_DOWNLOAD_URL" -o "$DB_PATH.tmp"; then
                mv "$DB_PATH.tmp" "$DB_PATH"
                echo "✅ Database downloaded successfully!"
                ls -lh "$DB_PATH"
                break
            else
                RETRY_COUNT=$((RETRY_COUNT + 1))
                echo "⚠️  Download failed (attempt $RETRY_COUNT/$MAX_RETRIES)"
                sleep 2
            fi
        done
        
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            echo "❌ Failed to download database after $MAX_RETRIES attempts"
            if [ ! -f "$DB_PATH" ]; then
                echo "⚠️  No existing database - server will start with empty database"
            else
                echo "ℹ️  Using existing database"
            fi
        fi
    else
        echo "⚠️  No database file found in release"
    fi
else
    echo "⚠️  No database releases found"
    if [ ! -f "$DB_PATH" ]; then
        echo "ℹ️  Will start with empty database"
    else
        echo "ℹ️  Using existing database"
    fi
fi

echo ""
echo "🔍 Database status:"
if [ -f "$DB_PATH" ]; then
    echo "   Path: $DB_PATH"
    echo "   Size: $(du -h "$DB_PATH" | cut -f1)"
    
    # Show database stats if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        echo "   Records:"
        sqlite3 "$DB_PATH" "SELECT granularity, COUNT(*) as count FROM sentiment_indices GROUP BY granularity;" 2>/dev/null || echo "     (Unable to query)"
    fi
else
    echo "   ⚠️  No database file present"
fi

echo ""
echo "🚀 Starting API server..."
echo ""

# Start the FastAPI server
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
