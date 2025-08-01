#!/usr/bin/env python3
"""
Simple HTTP request example for AfterIDE
"""

import requests

def main():
    print("Making HTTP request to httpbin.org...")
    
    try:
        # Make a simple GET request
        response = requests.get('https://httpbin.org/get')
        
        if response.status_code == 200:
            print("✅ Request successful!")
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response JSON: {response.json()}")
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 