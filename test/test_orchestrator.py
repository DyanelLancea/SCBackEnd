"""
Test script for Orchestrator Agent API
Run this after starting the server with: uvicorn app.main:app --reload

This script tests the orchestrator's message processing and intent detection.
"""
import requests
import json
import sys

# Fix Windows encoding issues with emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

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

def test_orchestrator_info():
    """Test orchestrator info endpoint"""
    print("\n🤖 Testing Orchestrator Info Endpoint...")
    response = requests.get(f"{BASE_URL}/orchestrator/")
    print_response("Orchestrator Info", response)
    return response.status_code == 200

def test_event_intent():
    """Test event-related intent detection"""
    print("\n🎉 Testing Event Intent Detection...")
    message_data = {
        "user_id": "test_user_123",
        "message": "What events are happening this weekend?"
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("Event Intent Test", response)
    
    # Check if intent was correctly detected
    if response.status_code == 200:
        data = response.json()
        if data.get("intent") == "find_events":
            print("✅ Correctly detected 'find_events' intent!")
        else:
            print(f"⚠️  Expected 'find_events' but got '{data.get('intent')}'")
    
    return response.status_code == 200

def test_emergency_intent():
    """Test emergency intent detection"""
    print("\n🚨 Testing Emergency Intent Detection...")
    message_data = {
        "user_id": "test_user_123",
        "message": "Help! I need emergency assistance"
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("Emergency Intent Test", response)
    
    # Check if intent was correctly detected
    if response.status_code == 200:
        data = response.json()
        if data.get("intent") == "emergency":
            print("✅ Correctly detected 'emergency' intent!")
        else:
            print(f"⚠️  Expected 'emergency' but got '{data.get('intent')}'")
    
    return response.status_code == 200

def test_sos_keyword():
    """Test SOS keyword detection"""
    print("\n🆘 Testing SOS Keyword Detection...")
    message_data = {
        "user_id": "test_user_456",
        "message": "SOS - need help immediately!"
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("SOS Keyword Test", response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("intent") == "emergency":
            print("✅ SOS keyword correctly triggered emergency intent!")
        else:
            print(f"⚠️  Expected 'emergency' but got '{data.get('intent')}'")
    
    return response.status_code == 200

def test_general_intent():
    """Test general/default intent"""
    print("\n💬 Testing General Intent Detection...")
    message_data = {
        "user_id": "test_user_789",
        "message": "Hello! How are you doing today?"
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print_response("General Intent Test", response)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("intent") == "general":
            print("✅ Correctly detected 'general' intent!")
        else:
            print(f"⚠️  Expected 'general' but got '{data.get('intent')}'")
    
    return response.status_code == 200

def test_conversation_history():
    """Test conversation history endpoint"""
    print("\n📚 Testing Conversation History Endpoint...")
    user_id = "test_user_123"
    response = requests.get(f"{BASE_URL}/orchestrator/history/{user_id}")
    print_response("Conversation History", response)
    return response.status_code == 200

def test_multiple_keywords():
    """Test message with multiple potential keywords"""
    print("\n🔍 Testing Multiple Keywords...")
    test_cases = [
        {
            "message": "Is there an event happening today?",
            "expected": "find_events",
            "description": "Event-related question"
        },
        {
            "message": "What activities are available?",
            "expected": "find_events",
            "description": "Activity-related question"
        },
        {
            "message": "I need help with an emergency",
            "expected": "emergency",
            "description": "Emergency help request"
        },
        {
            "message": "Can you help me find something to do?",
            "expected": "emergency",  # Currently "help" triggers emergency
            "description": "General help (may trigger emergency)"
        }
    ]
    
    results = []
    for test in test_cases:
        message_data = {
            "user_id": "test_user_multi",
            "message": test["message"]
        }
        response = requests.post(
            f"{BASE_URL}/orchestrator/message",
            json=message_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            detected = data.get("intent")
            match = "✅" if detected == test["expected"] else "⚠️"
            print(f"\n{match} {test['description']}")
            print(f"   Message: \"{test['message']}\"")
            print(f"   Expected: {test['expected']}, Got: {detected}")
            results.append(detected == test["expected"])
    
    return all(results)

def test_edge_cases():
    """Test edge cases"""
    print("\n⚡ Testing Edge Cases...")
    
    # Empty message
    print("\n  Testing empty message...")
    message_data = {
        "user_id": "test_user_edge",
        "message": ""
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"     Status: {response.status_code}")
    
    # Very long message
    print("\n  Testing very long message...")
    message_data = {
        "user_id": "test_user_edge",
        "message": "This is a very long message. " * 100
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"     Status: {response.status_code}")
    
    # Special characters
    print("\n  Testing special characters...")
    message_data = {
        "user_id": "test_user_edge",
        "message": "Hello! @#$%^&*() 你好 🎉"
    }
    response = requests.post(
        f"{BASE_URL}/orchestrator/message",
        json=message_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"     Status: {response.status_code}")
    
    return True

def run_basic_tests():
    """Run basic functionality tests"""
    print("\n" + "="*60)
    print("ORCHESTRATOR AGENT - BASIC TESTS")
    print("="*60)
    
    tests = [
        ("Info Endpoint", test_orchestrator_info),
        ("Event Intent", test_event_intent),
        ("Emergency Intent", test_emergency_intent),
        ("SOS Keyword", test_sos_keyword),
        ("General Intent", test_general_intent),
        ("Conversation History", test_conversation_history)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {str(e)}")
            results.append((name, False))
    
    return results

def run_advanced_tests():
    """Run advanced functionality tests"""
    print("\n" + "="*60)
    print("ORCHESTRATOR AGENT - ADVANCED TESTS")
    print("="*60)
    
    tests = [
        ("Multiple Keywords", test_multiple_keywords),
        ("Edge Cases", test_edge_cases)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {str(e)}")
            results.append((name, False))
    
    return results

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🤖 ORCHESTRATOR AGENT TEST SUITE")
    print("="*60)
    print(f"Testing API at: {BASE_URL}")
    print("\n⚠️  Make sure the server is running!")
    print("   Start with: uvicorn app.main:app --reload\n")
    
    try:
        # Check if server is accessible
        print("🔍 Checking server connection...")
        response = requests.get(f"{BASE_URL.replace('/api', '')}/")
        if response.status_code != 200:
            print("❌ Server not accessible!")
            return
        print("✅ Server is running!")
        
        # Run tests
        basic_results = run_basic_tests()
        advanced_results = run_advanced_tests()
        
        # Combine results
        all_results = basic_results + advanced_results
        
        # Print summary
        print_summary(all_results)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server!")
        print("   Make sure the server is running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()

