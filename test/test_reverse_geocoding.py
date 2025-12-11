import requests
import json
import asyncio
import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.safety.routes import reverse_geocode

BASE_URL = "http://localhost:8000/api/safety"

async def test_reverse_geocoding():
    """Test reverse geocoding function"""
    print("=" * 60)
    print("Testing Reverse Geocoding")
    print("=" * 60)
    
    # Test with Punggol Coast coordinates (Singapore)
    print("\n📍 Testing with Punggol Coast coordinates...")
    lat = 1.4056
    lon = 103.9025
    address = await reverse_geocode(lat, lon)
    print(f"Coordinates: {lat}, {lon}")
    print(f"Address: {address}")
    
    if address and "punggol" in address.lower():
        print("✅ Successfully geocoded to Punggol area!")
    elif address:
        print(f"✅ Got address: {address}")
    else:
        print("❌ Reverse geocoding failed")
    
    # Test with another Singapore location
    print("\n📍 Testing with Marina Bay coordinates...")
    lat = 1.2839
    lon = 103.8608
    address = await reverse_geocode(lat, lon)
    print(f"Coordinates: {lat}, {lon}")
    print(f"Address: {address}")
    
    if address:
        print(f"✅ Got address: {address}")
    else:
        print("❌ Reverse geocoding failed")

def test_location_update_and_get():
    """Test updating location and getting it back"""
    print("\n" + "=" * 60)
    print("Testing Location Update and Get")
    print("=" * 60)
    
    test_user_id = "test-user-device-location"
    
    # Step 1: Update location with device coordinates (Punggol Coast)
    print("\n📍 Step 1: Updating location with device GPS coordinates...")
    location_data = {
        "user_id": test_user_id,
        "latitude": 1.4056,  # Punggol Coast coordinates
        "longitude": 103.9025
    }
    
    response = requests.post(
        f"{BASE_URL}/location",
        json=location_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Location updated!")
        print(f"   Address stored: {data.get('address', 'N/A')}")
        print(f"   Full response: {json.dumps(data, indent=2)}")
    else:
        print(f"❌ Failed to update location: {response.text}")
        return
    
    # Step 2: Get the location back
    print("\n📍 Step 2: Getting location back...")
    response = requests.get(f"{BASE_URL}/location/{test_user_id}")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Location retrieved!")
        print(f"   Location display: {data.get('location_display', 'N/A')}")
        print(f"   Address: {data.get('address', 'N/A')}")
        print(f"   Coordinates: {data.get('latitude')}, {data.get('longitude')}")
        
        # Check if it's NOT "Kampung Centre"
        location_display = data.get('location_display', '').lower()
        if 'kampung' in location_display or 'centre' in location_display or 'center' in location_display:
            print("⚠️  WARNING: Still contains 'Kampung Centre' - this should be the actual location!")
        else:
            print("✅ Location is NOT hardcoded - showing actual device location!")
    else:
        print(f"❌ Failed to get location: {response.text}")

if __name__ == "__main__":
    print("⚠️  Make sure the backend server is running on http://localhost:8000")
    import time
    time.sleep(1)
    
    # Test reverse geocoding
    asyncio.run(test_reverse_geocoding())
    
    # Test location update and get
    test_location_update_and_get()
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
    print("\n💡 If location still shows 'Kampung Centre', the frontend needs to:")
    print("   1. Get device GPS coordinates")
    print("   2. Call POST /api/safety/location with coordinates")
    print("   3. Call GET /api/safety/location/{user_id} to get the address")
    print("   4. Display the 'location_display' field instead of hardcoded value")
    print("=" * 60)

