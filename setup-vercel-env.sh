#!/bin/bash
# Setup Vercel environment variables for GitHub Pages API
# Usage: ./setup-vercel-env.sh

set -e

# GitHub Pages URL (update with your actual GitHub username/repo)
BACKEND_URL="https://jtron780.github.io/BTC"

echo "🚀 Setting up Vercel environment variables"
echo ""
echo "GitHub Pages API URL: $BACKEND_URL"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "⚠️  Vercel CLI not installed"
    echo ""
    echo "Install with: npm i -g vercel"
    echo ""
    echo "Or manually add to Vercel dashboard:"
    echo "  Key: NEXT_PUBLIC_API_URL"
    echo "  Value: $BACKEND_URL"
    exit 1
fi

cd frontend

echo "Setting environment variable..."
vercel env add NEXT_PUBLIC_API_URL production <<< "$BACKEND_URL"
vercel env add NEXT_PUBLIC_API_URL preview <<< "$BACKEND_URL"

echo ""
echo "✅ Environment variable set!"
echo ""
echo "Now redeploy:"
echo "  cd frontend && vercel --prod"
echo ""
