#!/usr/bin/env python3
"""Test login API and verify JWT token generation."""
import requests
import json
import sys

def test_health():
    """Test health check endpoint."""
    print("=== Health Check ===")
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_login():
    """Test login endpoint."""
    print("\n=== Login Test ===")
    login_data = {
        "loginId": "admin@saas-platform.local",
        "password": "Admin@123"
    }
    
    try:
        response = requests.post(
            "http://localhost:8001/api/auth/login",
            json=login_data,
            timeout=5
        )
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Verify JWT token
            if "accessToken" in data and data["accessToken"]:
                print("\n✅ JWT Token successfully generated!")
                print(f"Token Type: {data.get('tokenType', 'N/A')}")
                print(f"Expires In: {data.get('expiresIn', 'N/A')} seconds")
                print(f"Access Token (first 50 chars): {data['accessToken'][:50]}...")
                return True
            else:
                print("\n❌ No access token in response")
                return False
        else:
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    health_ok = test_health()
    if not health_ok:
        print("\n❌ Health check failed. Make sure the server is running.")
        sys.exit(1)
    
    login_ok = test_login()
    if not login_ok:
        print("\n❌ Login test failed")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
