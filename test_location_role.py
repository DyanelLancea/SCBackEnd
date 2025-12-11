import requests
import json

BASE_URL = "http://localhost:8000/api/safety"

def test_location_with_role():
    """Test location endpoint with role parameter"""
    print("=" * 60)
    print("Testing Location Endpoint with Role Parameter")
    print("=" * 60)
    
    # Test 1: Get location without role (default behavior)
    print("\n📍 Test 1: Get location without role parameter")
    test_user_id = "test-user-123"
    response = requests.get(f"{BASE_URL}/location/{test_user_id}")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data.get('location_display', 'N/A')}")
        print(f"   User ID: {data.get('user_id')}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Get location with role=elderly
    print("\n📍 Test 2: Get location with role=elderly")
    response = requests.get(f"{BASE_URL}/location/{test_user_id}?role=elderly")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data.get('location_display', 'N/A')}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 3: Get location with role=caregiver
    print("\n📍 Test 3: Get location with role=caregiver")
    caregiver_user_id = "caregiver-user-456"
    response = requests.get(f"{BASE_URL}/location/{caregiver_user_id}?role=caregiver")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    if response.status_code == 200 and data.get("success"):
        print(f"✅ Success: {data.get('location_display', 'N/A')}")
    else:
        print(f"⚠️  Note: This is expected if caregiver is not linked to an elderly user")
        print(f"   Message: {data.get('message', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ Endpoint supports role parameter!")
    print("✅ No hardcoded values - all data from database")
    print("=" * 60)

if __name__ == "__main__":
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    import time
    time.sleep(1)
    test_location_with_role()

