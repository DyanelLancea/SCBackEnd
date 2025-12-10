"""
Test script for Safety Agent API
Run this after starting the server with: uvicorn app.main:app --reload
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_root():
    """Test root endpoint"""
    print("\n🔍 Testing Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    print_response("Root Endpoint", response)
    return response.status_code == 200

def test_sos():
    """Test SOS endpoint"""
    print("\n🚨 Testing SOS Endpoint...")
    sos_data = {
        "user_id": "test_user_123",
        "location": "123 Main Street, New York, NY",
        "message": "Emergency test - need help immediately"
    }
    response = requests.post(
        f"{BASE_URL}/safety/sos",
        json=sos_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("SOS Endpoint", response)
    return response.status_code == 200

def test_location():
    """Test location update endpoint"""
    print("\n📍 Testing Location Update Endpoint...")
    location_data = {
        "user_id": "test_user_123",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    response = requests.post(
        f"{BASE_URL}/safety/location",
        json=location_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("Location Update Endpoint", response)
    return response.status_code == 200

def test_status():
    """Test status endpoint"""
    print("\n📊 Testing Status Endpoint...")
    user_id = "test_user_123"
    response = requests.get(f"{BASE_URL}/safety/status/{user_id}")
    print_response("Status Endpoint", response)
    return response.status_code == 200

def main():
    """Run all tests"""
    print("\n" + "="*50)
    print("SAFETY AGENT API TEST SUITE")
    print("="*50)
    print(f"Testing API at: {BASE_URL}")
    print("\n⚠️  Make sure the server is running!")
    print("   Start with: uvicorn app.main:app --reload\n")
    
    try:
        # Test root
        if not test_root():
            print("\n❌ Root endpoint test failed. Is the server running?")
            return
        
        # Test SOS
        test_sos()
        
        # Test location
        test_location()
        
        # Test status
        test_status()
        
        print("\n" + "="*50)
        print("✅ All tests completed!")
        print("="*50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()

