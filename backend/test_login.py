#!/usr/bin/env python3
"""
Simple test script to check if login works
"""

import asyncio
import httpx
import json

async def test_login():
    """Test the login endpoint"""
    
    # Test different common credentials
    test_credentials = [
        {"username": "admin", "password": "admin123"},
        {"username": "admin", "password": "admin"},
        {"username": "test", "password": "test123"},
        {"username": "user", "password": "password"},
        {"username": "demo", "password": "demo123"},
    ]
    
    print("Testing login endpoint with different credentials...")
    
    async with httpx.AsyncClient() as client:
        for i, creds in enumerate(test_credentials, 1):
            print(f"\n--- Test {i}: {creds['username']} ---")
            
            try:
                response = await client.post(
                    "http://localhost:8000/api/v1/auth/login",
                    json=creds,
                    timeout=10.0
                )
                
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ Login successful!")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return True
                else:
                    print(f"❌ Login failed: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print("\n--- Testing registration ---")
    await test_registration(client)
    
    return False

async def test_registration(client):
    """Test the registration endpoint"""
    
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!"
    }
    
    try:
        response = await client.post(
            "http://localhost:8000/api/v1/auth/register",
            json=register_data,
            timeout=10.0
        )
        
        print(f"Registration status: {response.status_code}")
        print(f"Registration response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            # Now try to login with the new user
            print("\n--- Testing login with new user ---")
            login_response = await client.post(
                "http://localhost:8000/api/v1/auth/login",
                json={"username": "testuser", "password": "TestPass123!"},
                timeout=10.0
            )
            print(f"Login status: {login_response.status_code}")
            print(f"Login response: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Registration error: {e}")

if __name__ == "__main__":
    asyncio.run(test_login()) 