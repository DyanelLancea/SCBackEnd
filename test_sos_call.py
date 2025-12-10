"""
Test SOS Phone Call Feature
This script will trigger the SOS endpoint and make a real phone call.

Before running:
1. Make sure you have Twilio credentials set in your .env file:
   - TWILIO_ACCOUNT_SID
   - TWILIO_AUTH_TOKEN
   - (The phone number is hardcoded in the code)

2. Ensure your server is running:
   uvicorn app.main:app --reload

3. Make sure the emergency number (+6598631975) can receive calls
"""
import requests
import json
import os
import sys
from dotenv import load_dotenv

# Fix Windows encoding issues with emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

BASE_URL = "http://localhost:8000/api"

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

def test_sos_call():
    """Test SOS endpoint - This will make a REAL phone call!"""
    print("\n" + "="*60)
    print("🚨 SOS PHONE CALL TEST")
    print("="*60)
    print("\n⚠️  WARNING: This will make a REAL phone call!")
    print("   Emergency number: +6598631975")
    print("   Make sure you're ready to receive the call!\n")
    
    # Check Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not account_sid or not auth_token:
        print("❌ ERROR: Twilio credentials not found!")
        print("\nPlease add to your .env file:")
        print("TWILIO_ACCOUNT_SID=your_account_sid")
        print("TWILIO_AUTH_TOKEN=your_auth_token")
        print("\nGet these from: https://console.twilio.com/")
        return False
    
    print("✅ Twilio credentials found")
    print(f"   Account SID: {account_sid[:10]}...")
    if from_number:
        print(f"   From Number: {from_number}")
    
    print("\n⚠️  IMPORTANT: Make sure international calling is enabled in Twilio!")
    print("   Go to: https://www.twilio.com/console/voice/calls/geo-permissions/low-risk")
    print("   Enable calling to Singapore (+65)")
    
    # Ask for confirmation
    response = input("\nContinue with the test call? (yes/no): ").strip().lower()
    if response != 'yes':
        print("❌ Test cancelled")
        return False
    
    # Test data
    sos_data = {
        "user_id": "test_user_sos_call",
        "location": "Orchard Road, Singapore 238801",
        "message": "This is a test emergency alert. Please confirm you received this call and can hear the automated message clearly."
    }
    
    print(f"\n📞 Calling +6598631975...")
    print(f"   User ID: {sos_data['user_id']}")
    print(f"   Location: {sos_data['location']}")
    print(f"   Message: {sos_data['message']}")
    print("\n⏳ Making request...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/safety/sos",
            json=sos_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print_response("SOS Call Response", response)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SOS trigger successful!")
            
            if "call_successful" in data:
                if data["call_successful"]:
                    print("✅ Phone call was successfully initiated!")
                else:
                    print("❌ Phone call failed to initiate")
            
            if "alert_status" in data:
                print(f"\n📱 Call Status: {data['alert_status']}")
            
            if "error_details" in data and data["error_details"]:
                print(f"\n⚠️  Error Details: {data['error_details']}")
            
            if "call_from_number" in data:
                print(f"📱 Calling from: {data['call_from_number']}")
            
            if "emergency_call_initiated" in data:
                print(f"📞 Calling to: {data['emergency_call_initiated']}")
            
            if "call_sid" in data and data["call_sid"]:
                print(f"🔍 Call SID: {data['call_sid']}")
            
            if "call_successful" in data and data["call_successful"]:
                print("\n" + "="*60)
                print("📞 Check your phone now!")
                print("   You should receive a call on +6598631975")
                print("   The automated voice will speak:")
                print("   - Emergency alert details")
                print("   - Current time")
                print("   - Location information")
                print("   - User message")
                print("="*60)
            else:
                print("\n" + "="*60)
                print("❌ Phone call was not successful")
                if "error_details" in data and data["error_details"]:
                    print(f"\n💡 Suggestion: {data['error_details']}")
                print("="*60)
            return True
        else:
            print("\n❌ SOS trigger failed!")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def test_with_location_update():
    """First update location, then trigger SOS for more complete data"""
    print("\n" + "="*60)
    print("📍 UPDATING LOCATION FIRST...")
    print("="*60)
    
    location_data = {
        "user_id": "test_user_sos_call",
        "latitude": 1.3000,  # Singapore coordinates
        "longitude": 103.8000
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/safety/location",
            json=location_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✅ Location updated successfully")
            return True
        else:
            print(f"⚠️  Location update failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Location update error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SOS PHONE CALL TEST SCRIPT")
    print("="*60)
    print(f"\nTesting API at: {BASE_URL}")
    print("\n⚠️  Make sure:")
    print("   1. Server is running: uvicorn app.main:app --reload")
    print("   2. Twilio credentials are in .env file")
    print("   3. You're ready to receive a call on +6598631975\n")
    
    # Option to update location first
    update_location = input("Update location first? (yes/no): ").strip().lower()
    if update_location == 'yes':
        test_with_location_update()
    
    # Run the SOS call test
    test_sos_call()

