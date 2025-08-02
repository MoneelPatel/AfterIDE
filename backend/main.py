#!/usr/bin/env python3
"""
AfterIDE - Main Entry Point for Railway Deployment
This file serves as the main entry point for Railway deployment
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app from the app package
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting AfterIDE on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    print(f"🌐 Railway domain: {os.getenv('RAILWAY_PUBLIC_DOMAIN', 'not set')}")
    
    # Start the server using the imported app
    uvicorn.run(
        app,  # Use the imported app directly
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 