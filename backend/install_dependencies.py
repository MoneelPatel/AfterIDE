#!/usr/bin/env python3
"""
AfterIDE Dependency Installation Script
This script ensures all required packages are properly installed for Railway deployment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print(f"📄 Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with error: {e}")
        print(f"📄 Error output: {e.stderr}")
        return False

def verify_package(package_name, import_name=None):
    """Verify that a package is properly installed"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} is available")
        return True
    except ImportError as e:
        print(f"❌ {package_name} is NOT available: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 AfterIDE Dependency Installation Script")
    print("=" * 60)
    
    # Check Python version and environment
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"👤 User: {os.getenv('USER', 'unknown')}")
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        print("📁 Files in current directory:")
        for file in os.listdir("."):
            print(f"  - {file}")
        return False
    
    # Upgrade pip first
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements with verbose output
    print("\n📦 Installing requirements...")
    if not run_command("pip install -r requirements.txt --verbose", "Installing requirements"):
        print("❌ Failed to install requirements")
        return False
    
    # Verify key packages are installed
    print("\n🔍 Verifying key packages...")
    key_packages = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("redis", "redis"),
        ("psycopg2-binary", "psycopg2"),
        ("asyncpg", "asyncpg"),
        ("aiosqlite", "aiosqlite"),
        ("structlog", "structlog"),
        ("python-multipart", "multipart"),
        ("python-jose", "jose"),
        ("passlib", "passlib"),
        ("python-dotenv", "dotenv"),
        ("email-validator", "email_validator"),
        ("docker", "docker"),
        ("psutil", "psutil"),
        ("httpx", "httpx"),
    ]
    
    all_packages_available = True
    for package_name, import_name in key_packages:
        if not verify_package(package_name, import_name):
            all_packages_available = False
    
    if not all_packages_available:
        print("\n❌ Some packages are missing. Trying alternative installation...")
        
        # Try installing packages individually
        missing_packages = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "websockets==12.0",
            "sqlalchemy==2.0.23",
            "alembic==1.12.1",
            "psycopg2-binary==2.9.9",
            "asyncpg==0.29.0",
            "aiosqlite==0.19.0",
            "redis==5.0.1",
            "aioredis==2.0.1",
            "python-multipart==0.0.6",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-dotenv==1.0.0",
            "email-validator==2.1.0",
            "pydantic==2.5.0",
            "structlog==23.2.0",
            "docker==6.1.3",
            "psutil==5.9.6",
            "httpx==0.25.2"
        ]
        
        for package in missing_packages:
            if not run_command(f"pip install {package}", f"Installing {package}"):
                print(f"❌ Failed to install {package}")
                return False
        
        print("✅ Alternative installation completed")
    
    print("\n🎉 All dependencies installed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 