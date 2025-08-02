#!/usr/bin/env python3
"""
Test script to verify that the start command works correctly
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all necessary imports work"""
    try:
        print("Testing imports...")
        from app.main import app
        print("✅ Successfully imported app from app.main")
        
        # Test that the app has the expected attributes
        assert hasattr(app, 'get'), "App should have get method"
        print("✅ App has expected FastAPI methods")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_health_endpoint():
    """Test that the health endpoint is accessible"""
    try:
        from app.main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print("✅ Health endpoint is working")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health endpoint returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing AfterIDE startup...")
    
    success = True
    success &= test_imports()
    success &= test_health_endpoint()
    
    if success:
        print("🎉 All tests passed! The application should deploy successfully.")
    else:
        print("💥 Some tests failed. Please check the errors above.")
        sys.exit(1) 