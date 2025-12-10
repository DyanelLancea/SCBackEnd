"""
Test script for Singlish Processing Endpoint
Tests the /api/orchestrator/process-singlish endpoint

Run this after:
1. Installing dependencies: pip install -r requirements.txt
2. Setting OPENAI_API_KEY in your environment
3. Starting the server: uvicorn app.main:app --reload
"""
import requests
import json
import sys

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api"


def print_response(title, response):
    """Pretty print API response"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}")
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return data
    except:
        print(f"Response: {response.text}")
        return None


def test_text_input_basic():
    """Test basic Singlish text translation"""
    print("\n🧪 TEST 1: Basic Singlish Text Translation")
    print("Input: 'walao this uncle cut queue sia'")
    
    request_data = {
        "user_id": "test_user_123",
        "transcript": "walao this uncle cut queue sia"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Basic Singlish Translation", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def test_text_input_complex():
    """Test complex Singlish with mixed languages"""
    print("\n🧪 TEST 2: Complex Singlish (Mixed Languages)")
    print("Input: 'aiyo why like that one, so paiseh leh'")
    
    request_data = {
        "user_id": "test_user_456",
        "transcript": "aiyo why like that one, so paiseh leh"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Complex Singlish Translation", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def test_text_input_angry():
    """Test angry/frustrated Singlish"""
    print("\n🧪 TEST 3: Angry/Frustrated Sentiment")
    print("Input: 'siao liao! the bus broke down again, sibei jialat'")
    
    request_data = {
        "user_id": "test_user_789",
        "transcript": "siao liao! the bus broke down again, sibei jialat"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Angry Sentiment Analysis", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def test_text_input_happy():
    """Test happy/excited Singlish"""
    print("\n🧪 TEST 4: Happy/Excited Sentiment")
    print("Input: 'wah shiok ah! finally can makan at this place'")
    
    request_data = {
        "user_id": "test_user_abc",
        "transcript": "wah shiok ah! finally can makan at this place"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Happy Sentiment Analysis", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def test_text_input_polite():
    """Test polite/formal Singlish"""
    print("\n🧪 TEST 5: Polite Tone Detection")
    print("Input: 'excuse me ah, can help me check?'")
    
    request_data = {
        "user_id": "test_user_def",
        "transcript": "excuse me ah, can help me check?"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Polite Tone Detection", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def test_error_no_input():
    """Test error handling when no input provided"""
    print("\n🧪 TEST 6: Error Handling - No Input")
    
    request_data = {
        "user_id": "test_user_error"
        # No audio or transcript
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print_response("Error Test - No Input", response)
    
    if response.status_code == 400:
        print("\n✅ Correctly returned 400 error for missing input")
        return True
    else:
        print(f"\n❌ Expected 400 error, got {response.status_code}")
        return False


def test_error_empty_transcript():
    """Test error handling with empty transcript"""
    print("\n🧪 TEST 7: Error Handling - Empty Transcript")
    
    request_data = {
        "user_id": "test_user_error2",
        "transcript": ""
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    print_response("Error Test - Empty Transcript", response)
    
    if response.status_code == 400:
        print("\n✅ Correctly returned 400 error for empty transcript")
        return True
    else:
        print(f"\n❌ Expected 400 error, got {response.status_code}")
        return False


def test_malay_hokkien_mix():
    """Test Singlish with Malay and Hokkien words"""
    print("\n🧪 TEST 8: Malay + Hokkien Mix")
    print("Input: 'aiyah boh bian lah, just tahan one more week can already'")
    
    request_data = {
        "user_id": "test_user_mix",
        "transcript": "aiyah boh bian lah, just tahan one more week can already"
    }
    
    response = requests.post(
        f"{BASE_URL}/orchestrator/process-singlish",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    data = print_response("Malay + Hokkien Translation", response)
    
    if response.status_code == 200 and data:
        print("\n✅ Test Results:")
        print(f"   Original: {data.get('singlish_raw')}")
        print(f"   English:  {data.get('clean_english')}")
        print(f"   Sentiment: {data.get('sentiment')}")
        print(f"   Tone: {data.get('tone')}")
        return True
    else:
        print("\n❌ Test failed!")
        return False


def print_summary(results):
    """Print test summary"""
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for result in results if result)
    total = len(results)
    
    test_names = [
        "Basic Singlish Translation",
        "Complex Mixed Languages",
        "Angry Sentiment",
        "Happy Sentiment",
        "Polite Tone",
        "Error: No Input",
        "Error: Empty Transcript",
        "Malay + Hokkien Mix"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - Test {i}: {name}")
    
    print("\n" + "="*70)
    print(f"Results: {passed}/{total} tests passed")
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"Success Rate: {percentage:.1f}%")
    print("="*70)
    
    if passed == total:
        print("🎉 All tests passed! Singlish processing is working perfectly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed. Check the errors above.")


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🤖 SINGLISH PROCESSING TEST SUITE")
    print("="*70)
    print(f"Testing endpoint: {BASE_URL}/orchestrator/process-singlish")
    print("\n⚠️  Prerequisites:")
    print("   1. Server running: uvicorn app.main:app --reload")
    print("   2. OPENAI_API_KEY set in environment")
    print("   3. OpenAI package installed: pip install openai")
    
    try:
        # Check if server is accessible
        print("\n🔍 Checking server connection...")
        response = requests.get(f"{BASE_URL.replace('/api', '')}/")
        if response.status_code != 200:
            print("❌ Server not accessible!")
            return
        print("✅ Server is running!")
        
        # Run all tests
        results = [
            test_text_input_basic(),
            test_text_input_complex(),
            test_text_input_angry(),
            test_text_input_happy(),
            test_text_input_polite(),
            test_error_no_input(),
            test_error_empty_transcript(),
            test_malay_hokkien_mix()
        ]
        
        # Print summary
        print_summary(results)
        
        # Additional notes
        print("\n📝 Notes:")
        print("   • Translations may vary slightly depending on GPT-4's interpretation")
        print("   • Sentiment and tone analysis are AI-generated and may differ")
        print("   • Audio testing requires frontend integration")
        print("   • Each test makes a real API call to OpenAI (costs money)")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")


if __name__ == "__main__":
    main()

