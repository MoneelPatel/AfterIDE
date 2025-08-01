#!/usr/bin/env python3
"""
Simple test server for Railway deployment
This is a minimal FastAPI app to test if the deployment is working
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app
app = FastAPI(
    title="AfterIDE Test",
    description="Simple test server for Railway deployment",
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

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AfterIDE Test Server is running!",
        "status": "success",
        "port": os.getenv("PORT", "unknown"),
        "environment": os.getenv("RAILWAY_ENVIRONMENT_NAME", "unknown")
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Test server is running",
        "port": os.getenv("PORT", "unknown")
    }

@app.get("/test")
async def test():
    """Test endpoint"""
    return {
        "message": "Test endpoint working!",
        "railway_domain": os.getenv("RAILWAY_PUBLIC_DOMAIN", "not set"),
        "service_name": os.getenv("RAILWAY_SERVICE_NAME", "not set")
    }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting test server on port {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🌐 Railway domain: {os.getenv('RAILWAY_PUBLIC_DOMAIN', 'not set')}")
    
    uvicorn.run(
        "test_simple:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    ) 