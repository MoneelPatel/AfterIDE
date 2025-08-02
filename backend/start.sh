#!/bin/bash

# AfterIDE Railway Start Script
echo "🚀 Starting AfterIDE Backend..."

# Set Python path
export PYTHONPATH=/app

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found!"
    exit 1
fi

# Start the application
echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo "🌐 Port: $PORT"

# Run the application
exec python main.py 