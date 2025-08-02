#!/bin/bash

# AfterIDE - Railway Environment Check Script
# This script helps check and fix Railway environment variables

echo "🔍 Checking Railway environment variables..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

echo "✅ Railway CLI found"

# Check current environment variables
echo "📋 Current environment variables:"
railway variables

echo ""
echo "🔧 To fix the mixed content issue, ensure these variables are set correctly:"
echo ""
echo "   VITE_API_URL=https://sad-chess-production.up.railway.app/api/v1"
echo "   VITE_WS_URL=wss://sad-chess-production.up.railway.app"
echo ""

echo "💡 To set these variables, run:"
echo "   railway variables set VITE_API_URL=https://sad-chess-production.up.railway.app/api/v1"
echo "   railway variables set VITE_WS_URL=wss://sad-chess-production.up.railway.app"
echo ""

echo "🚀 After setting the variables, redeploy your application:"
echo "   railway up" 