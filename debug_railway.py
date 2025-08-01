#!/usr/bin/env python3
"""
AfterIDE Railway Debug Script
This script helps diagnose issues with Railway deployment
"""

import os
import sys
import subprocess
import socket
import requests
from datetime import datetime

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")

def check_environment():
    """Check environment variables and configuration"""
    print_section("Environment Check")
    
    print(f"📅 Timestamp: {datetime.now()}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")
    
    # Check Railway environment variables
    railway_vars = [
        'RAILWAY_PUBLIC_DOMAIN',
        'RAILWAY_PRIVATE_DOMAIN', 
        'RAILWAY_PROJECT_NAME',
        'RAILWAY_ENVIRONMENT_NAME',
        'RAILWAY_SERVICE_NAME',
        'PORT',
        'DATABASE_URL',
        'REDIS_URL'
    ]
    
    print("\n🚂 Railway Environment Variables:")
    for var in railway_vars:
        value = os.getenv(var, 'NOT SET')
        if 'PASSWORD' in var or 'SECRET' in var:
            value = '***HIDDEN***' if value != 'NOT SET' else value
        print(f"  {var}: {value}")

def check_ports():
    """Check which ports are listening"""
    print_section("Port Check")
    
    common_ports = [3000, 8000, 8080, 5000]
    port = int(os.getenv('PORT', 8000))
    
    print(f"🎯 Current PORT environment: {port}")
    
    for test_port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', test_port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {test_port} is open")
            else:
                print(f"❌ Port {test_port} is closed")
        except Exception as e:
            print(f"⚠️  Could not check port {test_port}: {e}")

def check_dependencies():
    """Check if required packages are installed"""
    print_section("Dependencies Check")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'redis'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is available")
        except ImportError as e:
            print(f"❌ {package} is NOT available: {e}")

def check_app_import():
    """Check if the app can be imported"""
    print_section("App Import Check")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Try to import the app
        from app.main import app
        print("✅ App imported successfully")
        
        # Check if app has required attributes
        if hasattr(app, 'routes'):
            print("✅ App has routes")
        else:
            print("⚠️  App doesn't have routes attribute")
            
    except Exception as e:
        print(f"❌ App import failed: {e}")
        print(f"📄 Full error: {e}")

def check_health_endpoint():
    """Check if health endpoint is accessible"""
    print_section("Health Endpoint Check")
    
    port = int(os.getenv('PORT', 8000))
    health_url = f"http://localhost:{port}/health"
    
    try:
        response = requests.get(health_url, timeout=5)
        print(f"✅ Health endpoint accessible: {response.status_code}")
        print(f"📄 Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ Health endpoint not accessible at {health_url}")
    except Exception as e:
        print(f"⚠️  Health check failed: {e}")

def main():
    """Main diagnostic function"""
    print("🚀 AfterIDE Railway Debug Script")
    print("=" * 60)
    
    check_environment()
    check_ports()
    check_dependencies()
    check_app_import()
    check_health_endpoint()
    
    print_section("Debug Complete")
    print("📋 Check the output above for any issues.")
    print("🔗 If you see errors, check Railway logs for more details.")

if __name__ == "__main__":
    main() 