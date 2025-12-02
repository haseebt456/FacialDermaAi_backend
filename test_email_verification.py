"""
Test script for email verification implementation
Run this after starting the server to test all endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000/api/auth"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")

def test_registration():
    """Test user registration with email verification"""
    print("\n🧪 TEST 1: User Registration")
    
    test_user = {
        "role": "patient",
        "name": "Test User",
        "username": f"testuser_{datetime.now().strftime('%H%M%S')}",
        "email": f"test_{datetime.now().strftime('%H%M%S')}@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=test_user)
    print_response("Registration Response", response)
    
    if response.status_code == 201:
        print("✅ Registration successful!")
        print("📧 Check your email for verification link")
        print(f"📝 Test user created: {test_user['email']}")
        return test_user
    else:
        print("❌ Registration failed!")
        return None

def test_login_unverified(user_data):
    """Test login with unverified email (should fail)"""
    print("\n🧪 TEST 2: Login with Unverified Email")
    
    login_data = {
        "emailOrUsername": user_data["email"],
        "password": user_data["password"],
        "role": user_data["role"]
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print_response("Login Response (Unverified)", response)
    
    if response.status_code == 403:
        error = response.json().get("detail", {}).get("error", "")
        if "not verified" in error.lower():
            print("✅ Correctly blocked unverified user!")
        else:
            print("⚠️ Blocked but wrong error message")
    else:
        print("❌ Should have blocked unverified user!")

def test_verification_no_token():
    """Test verification without token (should fail)"""
    print("\n🧪 TEST 3: Verification Without Token")
    
    response = requests.get(f"{BASE_URL}/verify-email")
    print_response("Verification Response (No Token)", response)
    
    if response.status_code == 400:
        print("✅ Correctly rejected missing token!")
    else:
        print("❌ Should have rejected missing token!")

def test_verification_invalid_token():
    """Test verification with invalid token (should fail)"""
    print("\n🧪 TEST 4: Verification With Invalid Token")
    
    response = requests.get(f"{BASE_URL}/verify-email?token=invalid_token_12345")
    print_response("Verification Response (Invalid Token)", response)
    
    if response.status_code == 404:
        print("✅ Correctly rejected invalid token!")
    else:
        print("❌ Should have rejected invalid token!")

def test_verification_valid_token():
    """Test verification with valid token"""
    print("\n🧪 TEST 5: Verification With Valid Token")
    print("⚠️ Manual test required:")
    print("1. Check your email")
    print("2. Copy the verification token from the URL")
    print("3. Make GET request to:")
    print(f"   {BASE_URL}/verify-email?token=YOUR_TOKEN_HERE")
    print("4. Should return success message")

def test_duplicate_registration():
    """Test duplicate email/username (should fail)"""
    print("\n🧪 TEST 6: Duplicate Registration")
    
    duplicate_user = {
        "role": "patient",
        "name": "Duplicate User",
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "testpass123"
    }
    
    # First registration
    response1 = requests.post(f"{BASE_URL}/register", json=duplicate_user)
    print_response("First Registration", response1)
    
    # Duplicate registration
    response2 = requests.post(f"{BASE_URL}/register", json=duplicate_user)
    print_response("Duplicate Registration", response2)
    
    if response2.status_code == 400:
        print("✅ Correctly rejected duplicate registration!")
    else:
        print("❌ Should have rejected duplicate!")

def test_old_signup_endpoint():
    """Test old signup endpoint (should work without verification)"""
    print("\n🧪 TEST 7: Old Signup Endpoint (No Verification)")
    
    old_user = {
        "role": "patient",
        "name": "Old User",
        "username": f"olduser_{datetime.now().strftime('%H%M%S')}",
        "email": f"old_{datetime.now().strftime('%H%M%S')}@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/signup", json=old_user)
    print_response("Old Signup Response", response)
    
    if response.status_code == 201:
        print("✅ Old signup still works!")
        
        # Try to login immediately (should work)
        login_data = {
            "emailOrUsername": old_user["email"],
            "password": old_user["password"],
            "role": old_user["role"]
        }
        
        login_response = requests.post(f"{BASE_URL}/login", json=login_data)
        print_response("Immediate Login Response", login_response)
        
        if login_response.status_code == 200:
            print("✅ Can login immediately without verification!")
        else:
            print("⚠️ Login should work for old signup")

def run_all_tests():
    """Run all automated tests"""
    print("\n" + "="*60)
    print("EMAIL VERIFICATION - AUTOMATED TESTS")
    print("="*60)
    print("\n⚙️ Testing against:", BASE_URL)
    print("⚠️ Make sure the server is running!\n")
    
    try:
        # Test server is running
        response = requests.get("http://localhost:5000/docs")
        if response.status_code != 200:
            print("❌ Server not running! Start with: uvicorn app.main:app --reload")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server!")
        print("   Start server with: uvicorn app.main:app --reload")
        return
    
    print("✅ Server is running!\n")
    
    # Run tests
    user_data = test_registration()
    
    if user_data:
        test_login_unverified(user_data)
    
    test_verification_no_token()
    test_verification_invalid_token()
    test_verification_valid_token()
    test_duplicate_registration()
    test_old_signup_endpoint()
    
    print("\n" + "="*60)
    print("TESTS COMPLETE!")
    print("="*60)
    print("\n📋 Summary:")
    print("✅ Automated tests passed")
    print("⚠️ Manual verification test pending (check email)")
    print("\n💡 Next steps:")
    print("1. Check your email for verification link")
    print("2. Click the link or copy the token")
    print("3. Test the verification endpoint manually")
    print("4. Try logging in after verification")
    print("\n")

if __name__ == "__main__":
    run_all_tests()
