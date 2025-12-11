"""
Diagnostic script to test SOS call functionality
Checks Twilio configuration and tests the SOS endpoint
"""

import os
import sys
from dotenv import load_dotenv
import httpx

# Load environment variables
load_dotenv()

def check_twilio_config():
    """Check if Twilio environment variables are set"""
    print("=" * 60)
    print("TWILIO CONFIGURATION CHECK")
    print("=" * 60)
    
    required_vars = {
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "TWILIO_PHONE_NUMBER": os.getenv("TWILIO_PHONE_NUMBER"),
        "SOS_EMERGENCY_NUMBER": os.getenv("SOS_EMERGENCY_NUMBER"),
    }
    
    all_set = True
    for var_name, var_value in required_vars.items():
        if var_value:
            # Mask sensitive values
            if "TOKEN" in var_name or "SID" in var_name:
                display_value = var_value[:8] + "..." if len(var_value) > 8 else "***"
            else:
                display_value = var_value
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"❌ {var_name}: NOT SET")
            all_set = False
    
    print()
    return all_set, required_vars

def test_sos_endpoint(base_url="http://localhost:8000", user_id="test-user-123"):
    """Test the SOS endpoint directly"""
    print("=" * 60)
    print("TESTING SOS ENDPOINT")
    print("=" * 60)
    
    url = f"{base_url}/api/safety/sos"
    payload = {
        "user_id": user_id,
        "location": "Test Location",
        "message": "Test SOS call"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print()
    
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        if response.status_code == 200:
            data = response.json()
            call_successful = data.get("call_successful", False)
            call_sid = data.get("call_sid")
            alert_status = data.get("alert_status", "")
            error_details = data.get("error_details")
            
            if call_successful:
                print("✅ SOS call was successfully initiated!")
                print(f"   Call SID: {call_sid}")
            else:
                print("❌ SOS call was NOT successful")
                print(f"   Alert Status: {alert_status}")
                if error_details:
                    print(f"   Error Details: {error_details}")
        else:
            print(f"❌ Endpoint returned error status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error calling SOS endpoint: {e}")
        import traceback
        traceback.print_exc()

def test_voice_sos_trigger(base_url="http://localhost:8000", user_id="test-user-123"):
    """Test voice endpoint triggering SOS"""
    print("=" * 60)
    print("TESTING VOICE ENDPOINT -> SOS TRIGGER")
    print("=" * 60)
    
    url = f"{base_url}/api/orchestrator/voice"
    payload = {
        "user_id": user_id,
        "transcript": "Help me, I need emergency assistance",
        "location": "Test Location"
    }
    
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    print()
    
    try:
        response = httpx.post(url, json=payload, timeout=30.0)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {result}")
        print()
        
        sos_triggered = result.get("sos_triggered", False)
        if sos_triggered:
            print("✅ Voice endpoint successfully triggered SOS!")
        else:
            print("❌ Voice endpoint did NOT trigger SOS")
            print(f"   Intent: {result.get('intent', 'unknown')}")
            print(f"   Message: {result.get('message', 'no message')}")
            
    except Exception as e:
        print(f"❌ Error calling voice endpoint: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SOS CALL DIAGNOSTIC TOOL")
    print("=" * 60 + "\n")
    
    # Check configuration
    all_set, config = check_twilio_config()
    
    if not all_set:
        print("\n⚠️  WARNING: Some Twilio environment variables are missing!")
        print("   Please set them in your .env file:")
        print("   - TWILIO_ACCOUNT_SID")
        print("   - TWILIO_AUTH_TOKEN")
        print("   - TWILIO_PHONE_NUMBER")
        print("   - SOS_EMERGENCY_NUMBER")
        print("\n   Get these from: https://console.twilio.com/")
        print()
    
    # Get base URL from environment or use default
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    user_id = os.getenv("TEST_USER_ID", "test-user-123")
    
    print(f"Using base URL: {base_url}")
    print(f"Using test user ID: {user_id}")
    print()
    
    # Test SOS endpoint directly
    test_sos_endpoint(base_url, user_id)
    
    print("\n" + "-" * 60 + "\n")
    
    # Test voice endpoint triggering SOS
    test_voice_sos_trigger(base_url, user_id)
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60 + "\n")

