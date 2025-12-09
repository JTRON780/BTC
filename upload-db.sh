#!/bin/bash
# Upload database to Railway using their CLI
# Usage: ./upload-db.sh

set -e

echo "🚀 Database Upload Helper"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    echo "Run: npm i -g @railway/cli"
    echo "Then run this script again."
    exit 1
fi

# Check if database exists
if [ ! -f "btc_sentiment.db" ]; then
    echo "❌ Database file 'btc_sentiment.db' not found!"
    exit 1
fi

echo "📦 Found database file ($(ls -lh btc_sentiment.db | awk '{print $5}'))"
echo ""
echo "Options:"
echo "  1) Upload to Railway (requires Railway project linked)"
echo "  2) Show manual upload instructions"
echo ""
read -p "Choose option (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "🔗 Linking to Railway project..."
        railway link
        
        echo ""
        echo "📤 Uploading database..."
        railway run --service backend "mkdir -p /data"
        railway run --service backend "cat > /data/btc_sentiment.db" < btc_sentiment.db
        
        echo ""
        echo "✅ Database uploaded successfully!"
        ;;
    2)
        echo ""
        echo "📋 Manual Upload Instructions:"
        echo ""
        echo "For Railway:"
        echo "  1. Install Railway CLI: npm i -g @railway/cli"
        echo "  2. Link project: railway link"
        echo "  3. Upload: railway run 'cat > /data/btc_sentiment.db' < btc_sentiment.db"
        echo ""
        echo "For Render.com:"
        echo "  Use their web UI to upload files to persistent disk"
        echo ""
        echo "For other platforms:"
        echo "  Use SCP/SFTP or their file upload mechanism"
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac
