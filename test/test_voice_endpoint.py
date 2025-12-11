"""
Test script for voice endpoint
Tests that the voice endpoint works correctly with transcripts
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_voice_with_transcript():
    """Test voice endpoint with transcript (recommended approach)"""
    print("\n🧪 Testing Voice Endpoint with Transcript...")
    
    test_data = {
        "user_id": "test-user-123",
        "transcript": "I want to book a workout event",
        "location": "Punggol Coast"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator/voice",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Voice endpoint works with transcript!")
            return True
        else:
            print(f"❌ Voice endpoint returned error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure backend is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_voice_without_transcript():
    """Test voice endpoint without transcript (should return 400, not 500)"""
    print("\n🧪 Testing Voice Endpoint without Transcript...")
    
    test_data = {
        "user_id": "test-user-123"
        # No transcript or audio
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/orchestrator/voice",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 400:
            print("✅ Correctly returns 400 (Bad Request) instead of 500")
            # Check that error message doesn't trigger frontend error detection
            error_detail = response.json().get("detail", "")
            if "OpenAI package" not in error_detail and "pip install" not in error_detail:
                print("✅ Error message is safe (won't trigger frontend error detection)")
                return True
            else:
                print("❌ Error message contains phrases that trigger frontend error detection")
                return False
        else:
            print(f"❌ Should return 400, but got {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure backend is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_orchestrator_info():
    """Test orchestrator info endpoint"""
    print("\n🧪 Testing Orchestrator Info Endpoint...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/orchestrator/",
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Voice Processing Available: {data.get('voice_processing_available', 'unknown')}")
        print(f"Audio Transcription Available: {data.get('audio_transcription_available', 'unknown')}")
        
        if response.status_code == 200 and data.get('voice_processing_available') == True:
            print("✅ Orchestrator info shows voice processing is available!")
            return True
        else:
            print("❌ Orchestrator info endpoint issue")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Voice Endpoint Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Orchestrator info
    results.append(("Orchestrator Info", test_orchestrator_info()))
    
    # Test 2: Voice with transcript (should work)
    results.append(("Voice with Transcript", test_voice_with_transcript()))
    
    # Test 3: Voice without transcript (should return 400, not 500)
    results.append(("Voice without Transcript", test_voice_without_transcript()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the output above.")
    print("=" * 60)

