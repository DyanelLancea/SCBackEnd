import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.safety.routes import reverse_geocode

async def test_address_formatting():
    """Test that addresses are formatted nicely"""
    print("=" * 60)
    print("Testing Address Formatting (Making it Look Nicer)")
    print("=" * 60)
    
    # Test with Bukit Timah / Holland Road coordinates
    print("\n📍 Testing with Bukit Timah area...")
    lat = 1.3314  # Bukit Timah / Holland Road area
    lon = 103.7856
    address = await reverse_geocode(lat, lon)
    print(f"Coordinates: {lat}, {lon}")
    print(f"Formatted Address: {address}")
    
    if address:
        # Check if it's nice and short (not the full long address)
        if len(address) < 50 and "," in address:
            print(f"✅ Nice format! Short and readable: '{address}'")
        elif len(address) < 30:
            print(f"✅ Nice format! Clean and concise: '{address}'")
        else:
            print(f"⚠️  Still a bit long: '{address}'")
    else:
        print("❌ No address returned")
    
    # Test with Punggol
    print("\n📍 Testing with Punggol area...")
    lat = 1.4056
    lon = 103.9025
    address = await reverse_geocode(lat, lon)
    print(f"Coordinates: {lat}, {lon}")
    print(f"Formatted Address: {address}")
    
    if address:
        print(f"✅ Format: '{address}'")
    
    # Test with Marina Bay
    print("\n📍 Testing with Marina Bay area...")
    lat = 1.2839
    lon = 103.8608
    address = await reverse_geocode(lat, lon)
    print(f"Coordinates: {lat}, {lon}")
    print(f"Formatted Address: {address}")
    
    if address:
        print(f"✅ Format: '{address}'")
    
    print("\n" + "=" * 60)
    print("Summary: Addresses should be short and readable")
    print("Example: 'Holland Road, Bukit Timah' instead of")
    print("         'Maple Lane, Holland Road, Bukit Timah, Central Region, Singapore, 279886, Singapore'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_address_formatting())

