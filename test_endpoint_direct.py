"""
Direct test to verify endpoint exists
"""
import requests
import json
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/orchestrator/process-singlish"

print("="*70)
print("Testing Endpoint Directly")
print("="*70)
print(f"\nEndpoint: {ENDPOINT}")

# Test 1: Check if endpoint exists (should get 405 Method Not Allowed for GET, not 404)
print("\n1. Testing GET request (should return 405, not 404)...")
try:
    response = requests.get(ENDPOINT, timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("   ❌ Endpoint NOT FOUND - Server needs restart!")
        print("\n   SOLUTION:")
        print("   1. Stop server (Ctrl+C in server terminal)")
        print("   2. Restart: uvicorn app.main:app --reload")
    elif response.status_code == 405:
        print("   [OK] Endpoint EXISTS (405 = method not allowed, which is correct)")
    else:
        print(f"   ⚠️  Unexpected status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Try POST with valid data
print("\n2. Testing POST request with transcript...")
try:
    data = {
        "user_id": "test_direct",
        "transcript": "walao this uncle cut queue sia"
    }
    print(f"   Sending: {json.dumps(data, indent=2)}")
    response = requests.post(
        ENDPOINT,
        json=data,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("   [OK] SUCCESS!")
        print(f"   Response:")
        print(f"   - Original: {result.get('singlish_raw')}")
        print(f"   - English:  {result.get('clean_english')}")
        print(f"   - Sentiment: {result.get('sentiment')}")
        print(f"   - Tone: {result.get('tone')}")
    elif response.status_code == 404:
        print("   ❌ Endpoint NOT FOUND - Server needs restart!")
    else:
        print(f"   ⚠️  Error status: {response.status_code}")
        try:
            error = response.json()
            print(f"   Error: {json.dumps(error, indent=2)}")
        except:
            print(f"   Error: {response.text[:500]}")
except requests.exceptions.Timeout:
    print("   ⚠️  Request timed out (OpenAI API might be slow)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Check API docs
print("\n3. Checking if endpoint appears in API docs...")
try:
    docs_response = requests.get(f"{BASE_URL}/docs", timeout=5)
    if "process-singlish" in docs_response.text:
        print("   [OK] Endpoint appears in API docs")
    else:
        print("   ❌ Endpoint NOT in API docs - server needs restart")
except Exception as e:
    print(f"   ⚠️  Could not check docs: {e}")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("\nIf endpoint returns 404:")
print("  → Stop server (Ctrl+C)")
print("  → Restart: uvicorn app.main:app --reload")
print("\nIf endpoint returns 500:")
print("  → Check OPENAI_API_KEY is set")
print("  → Check OpenAI package is installed")
print("\nIf endpoint works:")
print("  -> Everything is good! [OK]")

