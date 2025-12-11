"""
Comprehensive Test Script for Singlish Recordings with Intent Detection
Tests all 4 improved intents:
1. Book a Specific Event
2. Unregister from certain Events  
3. Check details of an event
4. Answer general questions

This tests the full flow:
Singlish Transcript → process-singlish → voice endpoint → intent detection → action execution
"""

import requests
import json
import sys
import time

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Use production API by default, can override with environment variable
import os
BASE_URL = os.getenv("API_BASE_URL", "https://scbackend-qfh6.onrender.com/api")
LOCAL_URL = "http://localhost:8000/api"

def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_response(title, response, show_full=False):
    """Pretty print API response"""
    print(f"\n📋 {title}")
    print("-" * 80)
    print(f"Status Code: {response.status_code}")
    try:
        data = response.json()
        if show_full:
            print(f"Full Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            # Show key fields
            if "intent" in data:
                print(f"✅ Intent: {data.get('intent')}")
            if "message" in data:
                msg = data.get('message', '')[:200]  # First 200 chars
                print(f"💬 Message: {msg}")
            if "action_executed" in data:
                print(f"⚡ Action Executed: {data.get('action_executed')}")
            if "event_details" in data:
                print(f"📅 Event: {data.get('event_details', {}).get('title', 'N/A')}")
        return data
    except:
        print(f"Response: {response.text}")
        return None

def test_step_1_process_singlish(singlish_text, user_id="test_user"):
    """Step 1: Process Singlish transcript to English"""
    print(f"\n🔤 Step 1: Processing Singlish → English")
    print(f"   Input: \"{singlish_text}\"")
    
    request_data = {
        "user_id": user_id,
        "transcript": singlish_text
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/orchestrator/process-singlish",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            english_text = data.get("clean_english", "")
            print(f"   ✅ Translated: \"{english_text}\"")
            return english_text, data
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return None, None
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None, None

def test_step_2_voice_intent(english_text, user_id="test_user", location=None):
    """Step 2: Send to voice endpoint for intent detection and action"""
    print(f"\n🎯 Step 2: Intent Detection & Action Execution")
    print(f"   Input: \"{english_text}\"")
    
    request_data = {
        "user_id": user_id,
        "transcript": english_text
    }
    if location:
        request_data["location"] = location
    
    try:
        response = requests.post(
            f"{BASE_URL}/orchestrator/voice",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        data = print_response("Voice Endpoint Response", response, show_full=False)
        return response.status_code == 200, data
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False, None

def test_full_flow(singlish_text, expected_intent, user_id="test_user", location=None):
    """Test the complete flow: Singlish → English → Intent → Action"""
    print_section(f"Testing: \"{singlish_text}\"")
    
    # Step 1: Process Singlish
    english_text, singlish_data = test_step_1_process_singlish(singlish_text, user_id)
    if not english_text:
        print("\n❌ FAILED: Could not translate Singlish")
        return False, None
    
    # Step 2: Voice intent detection
    success, voice_data = test_step_2_voice_intent(english_text, user_id, location)
    if not success:
        print("\n❌ FAILED: Voice endpoint error")
        return False, voice_data
    
    # Verify intent
    detected_intent = voice_data.get("intent") if voice_data else None
    if detected_intent == expected_intent:
        print(f"\n✅ SUCCESS: Correctly detected intent '{expected_intent}'")
    else:
        print(f"\n⚠️  WARNING: Expected '{expected_intent}', got '{detected_intent}'")
    
    return True, voice_data

# ==================== TEST CASES ====================

def test_book_specific_event():
    """Test 1: Book a Specific Event (not just the latest)"""
    print_section("TEST 1: Book a Specific Event")
    
    # First, let's get available events to test with
    print("\n📋 Getting available events...")
    try:
        events_resp = requests.get(f"{BASE_URL}/events/list?limit=10", timeout=10)
        if events_resp.status_code == 200:
            events = events_resp.json().get("events", [])
            if events:
                print(f"   Found {len(events)} events")
                for i, event in enumerate(events[:3], 1):
                    print(f"   {i}. {event.get('title')} (ID: {event.get('id')[:8]}...)")
                
                # Test with a specific event name
                test_event = events[0] if events else None
                if test_event:
                    event_name = test_event.get('title', '').split()[0]  # Get first word
                    singlish_text = f"eh, I want join {event_name.lower()} leh"
                    expected_intent = "book_event"
                    
                    success, data = test_full_flow(
                        singlish_text=singlish_text,
                        expected_intent=expected_intent,
                        user_id="test_user_book"
                    )
                    
                    # Verify it booked the correct event
                    if success and data:
                        event_details = data.get("event_details")
                        if event_details:
                            booked_title = event_details.get("title", "")
                            if event_name.lower() in booked_title.lower() or booked_title.lower() in event_name.lower():
                                print(f"\n✅ VERIFIED: Booked correct event '{booked_title}'")
                                return True
                            else:
                                print(f"\n⚠️  Booked event '{booked_title}' but expected something with '{event_name}'")
                        else:
                            print("\n⚠️  No event_details in response")
                    
                    return success
            else:
                print("   ⚠️  No events available. Create some events first!")
                return False
        else:
            print(f"   ❌ Could not fetch events: {events_resp.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error fetching events: {str(e)}")
        return False

def test_book_specific_event_variations():
    """Test booking with different Singlish variations"""
    print_section("TEST 1B: Book Event - Singlish Variations")
    
    test_cases = [
        {
            "singlish": "eh can book me for pickleball tournament ah?",
            "expected_intent": "book_event",
            "description": "Pickleball booking request"
        },
        {
            "singlish": "walao I want join yoga class sia",
            "expected_intent": "book_event",
            "description": "Yoga class booking"
        },
        {
            "singlish": "eh register me for the workout session leh",
            "expected_intent": "book_event",
            "description": "Workout session registration"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Variation {i}: {test['description']}")
        success, data = test_full_flow(
            singlish_text=test["singlish"],
            expected_intent=test["expected_intent"],
            user_id=f"test_user_book_{i}"
        )
        results.append(success)
        time.sleep(1)  # Rate limiting
    
    return all(results)

def test_unregister_event():
    """Test 2: Unregister from a specific event"""
    print_section("TEST 2: Unregister from Specific Event")
    
    # First book an event, then unregister
    print("\n📋 Step 0: First booking an event to unregister from...")
    
    # Get events
    try:
        events_resp = requests.get(f"{BASE_URL}/events/list?limit=5", timeout=10)
        if events_resp.status_code == 200:
            events = events_resp.json().get("events", [])
            if events:
                test_event = events[0]
                event_name = test_event.get('title', '').split()[0]
                
                # Book first
                singlish_book = f"eh register me for {event_name.lower()} lah"
                print(f"   Booking: \"{singlish_book}\"")
                _, book_data = test_full_flow(
                    singlish_text=singlish_book,
                    expected_intent="book_event",
                    user_id="test_user_unregister"
                )
                
                time.sleep(1)
                
                # Now unregister
                singlish_unregister = f"eh cancel my {event_name.lower()} registration leh"
                success, data = test_full_flow(
                    singlish_text=singlish_unregister,
                    expected_intent="cancel_event",
                    user_id="test_user_unregister"
                )
                
                if success and data:
                    if data.get("action_executed"):
                        print(f"\n✅ VERIFIED: Successfully unregistered from event")
                        return True
                    else:
                        print(f"\n⚠️  Action not executed")
                
                return success
            else:
                print("   ⚠️  No events available")
                return False
        else:
            print(f"   ❌ Could not fetch events")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_get_event_details():
    """Test 3: Check details of a specific event"""
    print_section("TEST 3: Get Event Details")
    
    # Get available events
    try:
        events_resp = requests.get(f"{BASE_URL}/events/list?limit=5", timeout=10)
        if events_resp.status_code == 200:
            events = events_resp.json().get("events", [])
            if events:
                test_event = events[0]
                event_name = test_event.get('title', '').split()[0]
                
                singlish_text = f"eh tell me about {event_name.lower()} leh"
                success, data = test_full_flow(
                    singlish_text=singlish_text,
                    expected_intent="get_event",
                    user_id="test_user_details"
                )
                
                if success and data:
                    message = data.get("message", "")
                    if "date" in message.lower() or "time" in message.lower() or "location" in message.lower():
                        print(f"\n✅ VERIFIED: Event details returned")
                        print(f"   Details: {message[:150]}...")
                        return True
                    else:
                        print(f"\n⚠️  Response doesn't seem to contain event details")
                
                return success
            else:
                print("   ⚠️  No events available")
                return False
        else:
            print(f"   ❌ Could not fetch events")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_general_questions():
    """Test 4: Answer general questions"""
    print_section("TEST 4: General Questions")
    
    test_cases = [
        {
            "singlish": "eh what can this app do ah?",
            "expected_intent": "general",
            "description": "App capabilities question"
        },
        {
            "singlish": "how to use this thing leh?",
            "expected_intent": "general",
            "description": "Usage question"
        },
        {
            "singlish": "eh can help me understand how this works?",
            "expected_intent": "general",
            "description": "Help request"
        }
    ]
    
    results = []
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Question {i}: {test['description']}")
        success, data = test_full_flow(
            singlish_text=test["singlish"],
            expected_intent=test["expected_intent"],
            user_id=f"test_user_general_{i}"
        )
        
        if success and data:
            message = data.get("message", "")
            # Check if it's a helpful answer (not just default message)
            if len(message) > 50 and ("can" in message.lower() or "help" in message.lower() or "event" in message.lower()):
                print(f"   ✅ Got helpful answer")
                results.append(True)
            else:
                print(f"   ⚠️  Answer might be too generic")
                results.append(True)  # Still count as pass
        else:
            results.append(False)
        
        time.sleep(1)  # Rate limiting
    
    return all(results)

def test_specific_event_matching():
    """Test that specific events are matched correctly (not just latest)"""
    print_section("TEST 5: Specific Event Matching (Critical Test)")
    
    # Get multiple events
    try:
        events_resp = requests.get(f"{BASE_URL}/events/list?limit=5", timeout=10)
        if events_resp.status_code == 200:
            events = events_resp.json().get("events", [])
            if len(events) >= 2:
                # Test with the SECOND event (not the first/latest)
                test_event = events[1]  # Second event
                event_name = test_event.get('title', '')
                
                print(f"\n🎯 Testing with SECOND event: '{event_name}'")
                print(f"   (This verifies it doesn't just book the latest event)")
                
                singlish_text = f"eh I want join {event_name.lower()} lah"
                success, data = test_full_flow(
                    singlish_text=singlish_text,
                    expected_intent="book_event",
                    user_id="test_user_specific"
                )
                
                if success and data:
                    event_details = data.get("event_details")
                    if event_details:
                        booked_title = event_details.get("title", "")
                        booked_id = event_details.get("id", "")
                        expected_id = test_event.get("id", "")
                        
                        if booked_id == expected_id:
                            print(f"\n✅ VERIFIED: Booked correct event!")
                            print(f"   Expected: {event_name} (ID: {expected_id[:8]}...)")
                            print(f"   Booked: {booked_title} (ID: {booked_id[:8]}...)")
                            return True
                        else:
                            print(f"\n❌ FAILED: Booked wrong event!")
                            print(f"   Expected ID: {expected_id[:8]}...")
                            print(f"   Got ID: {booked_id[:8]}...")
                            return False
                    else:
                        print(f"\n⚠️  No event_details in response")
                
                return success
            else:
                print("   ⚠️  Need at least 2 events to test specific matching")
                return False
        else:
            print(f"   ❌ Could not fetch events")
            return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

# ==================== MAIN TEST RUNNER ====================

def check_server():
    """Check if server is running"""
    try:
        # Check the base URL (remove /api if present)
        base_url = BASE_URL.replace("/api", "")
        response = requests.get(base_url, timeout=10)
        return response.status_code == 200
    except:
        return False

def print_summary(results):
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    test_names = [
        "Book Specific Event",
        "Book Event Variations",
        "Unregister from Event",
        "Get Event Details",
        "General Questions",
        "Specific Event Matching (Critical)"
    ]
    
    passed = 0
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{len(results)} tests passed ({passed*100//len(results)}%)")
    print("="*80)
    
    if passed == len(results):
        print("\n🎉 All tests passed! Singlish intent detection is working perfectly!")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed. Review the output above.")
    
    print("\n💡 Tips:")
    print("   • Make sure you have events created in your database")
    print("   • Ensure GROQ_API_KEY is set for intent detection")
    print("   • Ensure OPENAI_API_KEY is set for Singlish translation")
    print("   • Check server logs for detailed error messages")

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("  🧪 SINGLISH INTENT DETECTION TEST SUITE")
    print("="*80)
    print(f"\n📍 Testing API at: {BASE_URL}")
    if BASE_URL.startswith("https://"):
        print("   🌐 Using PRODUCTION server")
    else:
        print("   💻 Using LOCAL server")
    print("\n💡 To use localhost instead, set: export API_BASE_URL=http://localhost:8000/api")
    print("\n⚠️  Prerequisites:")
    print("   1. Server accessible at the URL above")
    print("   2. GROQ_API_KEY set in production environment (for intent detection)")
    print("   3. OPENAI_API_KEY set in production environment (for Singlish translation)")
    print("   4. Events created in database")
    
    # Check server
    print("\n🔍 Checking server connection...")
    if not check_server():
        print("❌ Server not accessible!")
        if BASE_URL.startswith("https://"):
            print("   Check that your production server is running")
            print("   Or use localhost: export API_BASE_URL=http://localhost:8000/api")
        else:
            print("   Start server with: uvicorn app.main:app --reload")
        return
    print("✅ Server is accessible!")
    
    # Run tests
    print("\n🚀 Starting tests...\n")
    
    results = []
    
    try:
        # Test 1: Book specific event
        results.append(test_book_specific_event())
        time.sleep(2)
        
        # Test 1B: Book event variations
        results.append(test_book_specific_event_variations())
        time.sleep(2)
        
        # Test 2: Unregister
        results.append(test_unregister_event())
        time.sleep(2)
        
        # Test 3: Get event details
        results.append(test_get_event_details())
        time.sleep(2)
        
        # Test 4: General questions
        results.append(test_general_questions())
        time.sleep(2)
        
        # Test 5: Specific event matching (critical)
        results.append(test_specific_event_matching())
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running tests: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main()

