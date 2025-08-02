#!/bin/bash

# AfterIDE - Fix Railway Environment Variables Script
# This script helps set the correct environment variables to fix mixed content issues

echo "🔧 Fixing Railway environment variables..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Railway CLI found"

# Check current project
echo "📋 Current project:"
railway status

echo ""
echo "🔧 Setting correct environment variables..."

# Set the correct environment variables
echo "Setting VITE_API_URL..."
railway variables set VITE_API_URL=https://sad-chess-production.up.railway.app/api/v1

echo "Setting VITE_WS_URL..."
railway variables set VITE_WS_URL=wss://sad-chess-production.up.railway.app

echo ""
echo "✅ Environment variables set successfully!"
echo ""
echo "📋 Current environment variables:"
railway variables

echo ""
echo "🚀 Now redeploy your application:"
echo "   railway up"
echo ""
echo "💡 If you're still having issues, try:"
echo "   1. Clear your browser cache"
echo "   2. Use the 'Reset Auth' button in the app"
echo "   3. Log in again" 