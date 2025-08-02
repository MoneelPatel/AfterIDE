#!/bin/bash

# AfterIDE - API Test Script
# This script tests the API endpoints to verify they're working correctly

echo "🧪 Testing API endpoints..."

# Test the health endpoint
echo "Testing health endpoint..."
curl -s https://sad-chess-production.up.railway.app/health

echo ""
echo "Testing API base endpoint..."
curl -s https://sad-chess-production.up.railway.app/api/v1/

echo ""
echo "✅ API tests completed!"
echo ""
echo "💡 If you see errors, check:"
echo "   1. The backend service is running"
echo "   2. The environment variables are set correctly"
echo "   3. The CORS settings allow your frontend domain" 