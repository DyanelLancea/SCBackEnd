"""
Test Emergency Message Integration
Tests that the backend correctly uses frontend's ready-to-use emergency messages.

IMPORTANT: Make sure your backend server is running before running this test!
Start it with: python -m uvicorn app.main:app --reload
"""

import requests
import json
import sys
import os
from datetime import datetime

# Set UTF-8 encoding for Windows console compatibility
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

# Configuration
BASE_URL = "http://localhost:8000"  # Change to your backend URL
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

def print_section(title):
    """Print a formatted section header"""
    # Remove emoji characters for Windows compatibility
    title_clean = title.replace("1️⃣", "1").replace("2️⃣", "2").replace("3️⃣", "3").replace("4️⃣", "4").replace("5️⃣", "5").replace("6️⃣", "6").replace("📊", "SUMMARY")
    print("\n" + "=" * 60)
    print(f"  {title_clean}")
    print("=" * 60)

def print_result(success, message):
    """Print a formatted result"""
    icon = "[OK]" if success else "[FAIL]"
    print(f"   {icon} {message}")

def test_sos_with_message_field():
    """Test 1: SOS with frontend's message field"""
    print_section("1️⃣ Testing SOS with 'message' field")
    
    request_body = {
        "user_id": TEST_USER_ID,
        "alert_type": "sos",
        "latitude": 1.410576,
        "longitude": 103.893386,
        "location": "Lat: 1.410576, Lng: 103.893386",
        "message": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386).",
        "text": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/safety/sos",
            json=request_body,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=4)}")
            
            if data.get("success"):
                print_result(True, "SOS request accepted")
                print_result(True, f"Alert triggered: {data.get('alert_triggered', False)}")
                
                # Check if message was processed (backend should use it)
                if data.get("call_sid"):
                    print_result(True, f"Twilio call initiated: {data.get('call_sid')}")
                else:
                    print_result(False, "Twilio call not initiated (may be due to missing Twilio config)")
                
                return True
            else:
                print_result(False, "SOS request failed")
                return False
        else:
            print_result(False, f"HTTP Error {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {json.dumps(error_data, indent=4)}")
            except:
                print(f"   Error text: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_result(False, "Cannot connect to backend. Is the server running?")
        print(f"   Tried to connect to: {BASE_URL}")
        return False
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_sos_with_text_field_only():
    """Test 2: SOS with 'text' field only (no 'message')"""
    print_section("2️⃣ Testing SOS with 'text' field only")
    
    request_body = {
        "user_id": TEST_USER_ID,
        "alert_type": "sos",
        "latitude": 1.410576,
        "longitude": 103.893386,
        "text": "Emergency SOS activated. Location: Seletar Link, Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/safety/sos",
            json=request_body,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_result(True, "SOS request accepted with 'text' field")
                return True
            else:
                print_result(False, "SOS request failed")
                return False
        else:
            print_result(False, f"HTTP Error {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_sos_without_message():
    """Test 3: SOS without message/text (should use fallback)"""
    print_section("3️⃣ Testing SOS without message/text (fallback)")
    
    request_body = {
        "user_id": TEST_USER_ID,
        "alert_type": "sos",
        "location": "Singapore"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/safety/sos",
            json=request_body,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print_result(True, "SOS request accepted (using fallback message)")
                print("   → Backend should build message from location and timestamp")
                return True
            else:
                print_result(False, "SOS request failed")
                return False
        else:
            print_result(False, f"HTTP Error {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_orchestrator_emergency():
    """Test 4: Emergency via orchestrator with message field"""
    print_section("4️⃣ Testing Emergency via Orchestrator with 'message' field")
    
    request_body = {
        "user_id": TEST_USER_ID,
        "message": "help",
        "location": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator/message",
            json=request_body,
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=4)}")
            
            if data.get("sos_triggered") or data.get("action_executed"):
                print_result(True, "Emergency detected and processed")
                return True
            else:
                print_result(False, "Emergency not triggered")
                return False
        else:
            print_result(False, f"HTTP Error {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Exception: {str(e)}")
        return False

def test_message_format_examples():
    """Test 5: Test different message formats"""
    print_section("5️⃣ Testing Different Message Formats")
    
    test_messages = [
        {
            "name": "Full address with MRT",
            "message": "Emergency SOS activated. Location: 123 Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
        },
        {
            "name": "Road name with MRT",
            "message": "Emergency SOS activated. Location: Seletar Link, Seletar near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
        },
        {
            "name": "Only MRT and coordinates",
            "message": "Emergency SOS activated. Location: near Punggol Coast MRT (Lat: 1.410576, Lng: 103.893386)."
        },
        {
            "name": "Only coordinates",
            "message": "Emergency SOS activated. Location: Lat: 1.410576, Lng: 103.893386."
        },
        {
            "name": "Location unavailable",
            "message": "Emergency SOS activated. Location unavailable."
        }
    ]
    
    results = []
    for test_case in test_messages:
        print(f"\n   Testing: {test_case['name']}")
        request_body = {
            "user_id": TEST_USER_ID,
            "alert_type": "sos",
            "message": test_case["message"]
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/safety/sos",
                json=request_body,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print_result(True, f"Accepted: {test_case['name']}")
                    results.append(True)
                else:
                    print_result(False, f"Failed: {test_case['name']}")
                    results.append(False)
            else:
                print_result(False, f"HTTP {response.status_code}: {test_case['name']}")
                results.append(False)
        except Exception as e:
            print_result(False, f"Exception: {test_case['name']} - {str(e)}")
            results.append(False)
    
    return all(results)

def test_endpoint_availability():
    """Test 6: Check endpoint availability"""
    print_section("6️⃣ Testing Endpoint Availability")
    
    endpoints = [
        ("POST", "/api/safety/sos"),
        ("POST", "/api/safety/emergency"),
        ("POST", "/api/orchestrator/message"),
    ]
    
    for method, endpoint in endpoints:
        try:
            response = requests.request(
                method,
                f"{BASE_URL}{endpoint}",
                json={"user_id": TEST_USER_ID},
                timeout=5
            )
            status = response.status_code
            if status < 500:  # 2xx, 3xx, 4xx are all "endpoint exists"
                print_result(True, f"{method} {endpoint}: {status}")
            else:
                print_result(False, f"{method} {endpoint}: {status} (Server Error)")
        except requests.exceptions.ConnectionError:
            print_result(False, f"{method} {endpoint}: Cannot connect")
        except Exception as e:
            print_result(False, f"{method} {endpoint}: {str(e)}")

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  EMERGENCY MESSAGE INTEGRATION TEST")
    print("=" * 60)
    print(f"\n   Backend URL: {BASE_URL}")
    print(f"   Test User ID: {TEST_USER_ID}")
    print("\n   Make sure to update BASE_URL if your backend is running elsewhere!")
    
    results = []
    
    # Run tests
    results.append(("SOS with message field", test_sos_with_message_field()))
    results.append(("SOS with text field only", test_sos_with_text_field_only()))
    results.append(("SOS without message (fallback)", test_sos_without_message()))
    results.append(("Orchestrator emergency", test_orchestrator_emergency()))
    results.append(("Different message formats", test_message_format_examples()))
    test_endpoint_availability()
    
    # Summary
    print_section("📊 Test Summary")
    for test_name, passed in results:
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"   {test_name}: {status}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n   Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n   [SUCCESS] All tests passed! Emergency message integration is working.")
    else:
        print("\n   [FAILED] Some tests failed. Check the errors above.")
        print("\n   Troubleshooting:")
        print("   1. Make sure backend server is running")
        print("   2. Check backend logs for errors")
        print("   3. Verify SOSRequest model accepts all fields")
        print("   4. Check if message handling logic is correct")
    
    print("\n" + "=" * 60 + "\n")
    
    return passed_count == total_count

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARNING] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

