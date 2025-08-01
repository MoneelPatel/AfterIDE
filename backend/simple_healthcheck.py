#!/usr/bin/env python3
"""
Simple health check script for AfterIDE backend
This script checks if the application is running without importing the app module
"""

import sys
import os
import time
import socket

def check_port(port):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Port check failed: {e}")
        return False

def main():
    """Main health check function"""
    # Get port from environment or default to 8000
    port = int(os.getenv('PORT', 8000))
    
    print(f"🔍 Checking if application is running on port {port}...")
    
    # Check if port is open
    if check_port(port):
        print("✅ Port is open - application appears to be running")
        sys.exit(0)
    else:
        print("❌ Port is not open - application may not be running")
        sys.exit(1)

if __name__ == "__main__":
    main() 