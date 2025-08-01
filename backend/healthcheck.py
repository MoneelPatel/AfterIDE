#!/usr/bin/env python3
"""
Health check script for AfterIDE backend
This script checks if the FastAPI application is running and responding
"""

import sys
import os
import time
from urllib.request import urlopen, URLError
from urllib.parse import urlparse

def check_health():
    """Check if the application is healthy"""
    try:
        # Get port from environment or default to 8000
        port = os.getenv('PORT', '8000')
        health_url = f"http://localhost:{port}/health"
        
        # Try to connect to the health endpoint
        with urlopen(health_url, timeout=10) as response:
            if response.getcode() == 200:
                print("Health check passed: Application is running")
                return True
            else:
                print(f"Health check failed: HTTP {response.getcode()}")
                return False
                
    except URLError as e:
        print(f"Health check failed: {e}")
        return False
    except Exception as e:
        print(f"Health check failed with exception: {e}")
        return False

if __name__ == "__main__":
    # Give the application a bit more time to start up
    time.sleep(2)
    
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1) 