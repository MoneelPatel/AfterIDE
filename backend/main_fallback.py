#!/usr/bin/env python3
"""
AfterIDE - Fallback Main Entry Point for Railway Deployment
This file serves as a fallback entry point that works without pydantic-settings
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import the original app, fallback to alternative if needed
try:
    print("🔍 Trying to import original app...")
    from app.main import app
    print("✅ Original app imported successfully")
except ImportError as e:
    print(f"⚠️  Original app import failed: {e}")
    print("🔄 Trying fallback approach...")
    
    # Try to use alternative config
    try:
        # Temporarily replace the config import
        import app.core.config_alt as config_alt
        import app.core.config as original_config
        
        # Replace the settings in the original config module
        original_config.settings = config_alt.settings
        print("✅ Alternative config loaded successfully")
        
        # Now try to import the app again
        from app.main import app
        print("✅ App imported with alternative config")
    except Exception as e2:
        print(f"❌ Fallback approach also failed: {e2}")
        print("🚨 Creating minimal FastAPI app...")
        
        # Create a minimal FastAPI app as last resort
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(
            title="AfterIDE",
            description="AfterIDE - Web-Based Integrated Development Environment",
            version="1.0.0"
        )
        
        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "version": "1.0.0",
                "environment": "production",
                "note": "running with minimal configuration"
            }
        
        @app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "AfterIDE is running with minimal configuration"}

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting AfterIDE on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python path: {sys.path}")
    
    # Start the server
    uvicorn.run(
        "main_fallback:app",  # Use this file as the entry point
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    ) 