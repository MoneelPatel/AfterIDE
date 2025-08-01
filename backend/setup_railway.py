#!/usr/bin/env python3
"""
AfterIDE Railway Setup Script
This script ensures all dependencies are properly installed for Railway deployment
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"📄 Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error: {e}")
        print(f"📄 Error output: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 AfterIDE Railway Setup Script")
    print("=" * 40)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # List files in current directory
    print("📁 Files in current directory:")
    for file in os.listdir("."):
        print(f"  - {file}")
    
    # Upgrade pip
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements - try railway requirements first, fallback to regular
    requirements_file = "requirements-railway.txt"
    if not os.path.exists(requirements_file):
        requirements_file = "requirements.txt"
        print(f"⚠️  {requirements_file} not found, using requirements.txt")
    
    if not run_command(f"pip install -r {requirements_file}", f"Installing requirements from {requirements_file}"):
        return False
    
    # Try to install pydantic-settings specifically if it fails
    print("🔍 Checking pydantic-settings installation...")
    try:
        import pydantic_settings
        print("✅ pydantic-settings is available")
    except ImportError:
        print("⚠️  pydantic-settings not found, trying to install it...")
        if not run_command("pip install pydantic-settings==2.1.0", "Installing pydantic-settings"):
            print("❌ Failed to install pydantic-settings")
            return False
    
    # Verify key packages are installed
    key_packages = [
        "fastapi",
        "uvicorn", 
        "pydantic",
        "sqlalchemy",
        "redis"
    ]
    
    print("🔍 Verifying key packages...")
    for package in key_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is available")
        except ImportError as e:
            print(f"❌ {package} is NOT available: {e}")
            return False
    
    print("✅ All key packages are available!")
    
    # Test importing the app
    print("🔍 Testing app import...")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.main import app
        print("✅ App import successful!")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        print(f"📄 Full error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 