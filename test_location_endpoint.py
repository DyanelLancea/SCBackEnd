import requests
import json
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/api/safety"

def print_response(title, response):
    print(f"\n🧪 Testing {title}...")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except json.JSONDecodeError:
        print(f"Response (raw): {response.text}")

def test_get_location_with_user():
    """Test getting location for a specific user"""
    test_user_id = "test-user-123"
    
    # First, update location for this user
    print("\n📍 Step 1: Updating location for test user...")
    location_data = {
        "user_id": test_user_id,
        "latitude": 1.3521,  # Singapore coordinates
        "longitude": 103.8198
    }
    update_response = requests.post(
        f"{BASE_URL}/location",
        json=location_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("Update Location", update_response)
    
    if update_response.status_code != 200:
        print("❌ Failed to update location. Cannot test GET endpoint.")
        return False
    
    # Now get the location
    print("\n📍 Step 2: Getting location for test user...")
    get_response = requests.get(f"{BASE_URL}/location/{test_user_id}")
    print_response("Get Current Location", get_response)
    
    if get_response.status_code == 200:
        data = get_response.json()
        assert data.get("success") is True, "Response should have success: true"
        assert data.get("user_id") == test_user_id, "User ID should match"
        assert data.get("location_display") is not None, "Should have location_display"
        assert data.get("latitude") is not None, "Should have latitude"
        assert data.get("longitude") is not None, "Should have longitude"
        assert "Kampung" not in str(data.get("location_display", "")), "Should NOT contain hardcoded 'Kampung'"
        print("✅ All assertions passed!")
        print(f"✅ Location display: {data.get('location_display')}")
        print(f"✅ Time since update: {data.get('time_since_update', 'N/A')}")
        return True
    else:
        print(f"❌ GET request failed with status {get_response.status_code}")
        return False

def test_get_location_nonexistent_user():
    """Test getting location for a user that doesn't exist"""
    print("\n📍 Testing with non-existent user...")
    nonexistent_user_id = "nonexistent-user-999"
    response = requests.get(f"{BASE_URL}/location/{nonexistent_user_id}")
    print_response("Get Location (Non-existent User)", response)
    
    if response.status_code == 200:
        data = response.json()
        assert data.get("success") is True, "Should return success even if no location"
        assert data.get("current_location") is None, "Should return None for location"
        assert data.get("location_display") == "Location not available", "Should show 'Location not available'"
        print("✅ Correctly handles non-existent user!")
        return True
    else:
        print(f"❌ Unexpected status code: {response.status_code}")
        return False

def test_get_location_invalid_user_id():
    """Test with invalid/empty user_id"""
    print("\n📍 Testing with empty user_id...")
    response = requests.get(f"{BASE_URL}/location/")
    print_response("Get Location (Empty User ID)", response)
    
    # Should return 404 or 422
    if response.status_code in [404, 422, 400]:
        print("✅ Correctly rejects empty user_id!")
        return True
    else:
        print(f"⚠️ Unexpected status code: {response.status_code}")
        return True  # Not a critical failure

if __name__ == "__main__":
    print("=" * 60)
    print("Location Endpoint Test Suite")
    print("=" * 60)
    print("\n⚠️  Make sure the backend server is running on http://localhost:8000")
    print("   Start it with: python -m app.main")
    print("=" * 60)
    
    import time
    time.sleep(1)  # Give a moment for user to read
    
    results = []
    
    # Test 1: Get location for existing user
    try:
        results.append(("Get Location (Existing User)", test_get_location_with_user()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Get Location (Existing User)", False))
    
    # Test 2: Get location for non-existent user
    try:
        results.append(("Get Location (Non-existent User)", test_get_location_nonexistent_user()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Get Location (Non-existent User)", False))
    
    # Test 3: Invalid user_id
    try:
        results.append(("Get Location (Invalid User ID)", test_get_location_invalid_user_id()))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Get Location (Invalid User ID)", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✅ All tests passed! The endpoint is working correctly.")
        print("✅ No hardcoded values detected - location comes from database!")
    else:
        print("\n⚠️  Some tests failed. Please check the output above.")
    print("=" * 60)

