#!/usr/bin/env python3
"""
AfterIDE - Start Script for Railway/Nixpacks
This file serves as an alternative entry point for deployment
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main application
if __name__ == "__main__":
    from main import app
    import uvicorn
    
    # Get port from environment variable
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting AfterIDE on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 