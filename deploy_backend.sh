#!/bin/bash

# AfterIDE Backend Deployment Script
echo "🚀 Deploying AfterIDE Backend to Railway..."

# Check if we're in the right directory
if [ ! -f "railway.toml" ]; then
    echo "❌ Error: railway.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Please commit them before deploying."
    echo "   Run: git add . && git commit -m 'Prepare for deployment'"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ Deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Check Railway dashboard for deployment status"
echo "2. Set environment variables in Railway:"
echo "   - SECRET_KEY=your-super-secret-key-here"
echo "   - POSTGRES_PASSWORD=your-secure-password"
echo "3. Test the deployment at:"
echo "   - Health: https://your-app-name.up.railway.app/health"
echo "   - API Docs: https://your-app-name.up.railway.app/docs"
echo "   - Root: https://your-app-name.up.railway.app/"
echo ""
echo "🔗 Once backend is working, we can deploy the frontend as a separate service." 