#!/bin/bash

# AfterIDE Backend Startup Script
# This script ensures the application starts correctly in Railway

set -e

echo "🚀 Starting AfterIDE Backend..."

# Set Python path to include current directory
export PYTHONPATH=/app

# Create necessary directories
mkdir -p /tmp/afteride

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: app/main.py not found. Current directory: $(pwd)"
    echo "📁 Contents of current directory:"
    ls -la
    exit 1
fi

echo "✅ Found app/main.py, starting uvicorn..."

# Start the application
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 