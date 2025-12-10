"""
Actually test Render deployment - not just print info
"""
import requests
import sys
import json
from urllib.parse import urlparse

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Get Render URL from user or use default
RENDER_URL = input("Enter your Render app URL (e.g., https://your-app.onrender.com): ").strip()
if not RENDER_URL:
    print("❌ No URL provided. Exiting.")
    sys.exit(1)

# Remove trailing slash
RENDER_URL = RENDER_URL.rstrip('/')

print(f"\n{'='*70}")
print(f"Testing Render Deployment: {RENDER_URL}")
print(f"{'='*70}\n")

results = {
    "base_url": RENDER_URL,
    "tests": []
}

def test_endpoint(name, method, path, expected_status=None, data=None):
    """Test an endpoint and return results"""
    url = f"{RENDER_URL}{path}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"}, timeout=30)
        else:
            return {"error": f"Unknown method: {method}"}
        
        status = response.status_code
        try:
            response_data = response.json()
        except:
            response_data = response.text[:200]
        
        result = {
            "name": name,
            "url": url,
            "method": method,
            "status": status,
            "expected": expected_status,
            "success": status == expected_status if expected_status else status < 400,
            "response": response_data
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "url": url,
            "method": method,
            "status": "TIMEOUT",
            "success": False,
            "error": "Request timed out"
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "url": url,
            "method": method,
            "status": "CONNECTION_ERROR",
            "success": False,
            "error": "Could not connect to server"
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "method": method,
            "status": "ERROR",
            "success": False,
            "error": str(e)
        }

# Test 1: Base health check
print("1. Testing base health endpoint...")
result = test_endpoint("Health Check", "GET", "/health", expected_status=200)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - Server is running")
else:
    print(f"   ❌ {result.get('status', 'ERROR')} - {result.get('error', 'Health check failed')}")

# Test 2: Root endpoint
print("\n2. Testing root endpoint...")
result = test_endpoint("Root", "GET", "/", expected_status=200)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - Root endpoint works")
else:
    print(f"   ❌ {result.get('status', 'ERROR')} - Root endpoint failed")

# Test 3: Orchestrator info
print("\n3. Testing orchestrator info endpoint...")
result = test_endpoint("Orchestrator Info", "GET", "/api/orchestrator/", expected_status=200)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - Orchestrator module loaded")
else:
    print(f"   ❌ {result.get('status', 'ERROR')} - Orchestrator module not found")

# Test 4: Test route (simple endpoint)
print("\n4. Testing test-route endpoint...")
result = test_endpoint("Test Route", "GET", "/api/orchestrator/test-route", expected_status=200)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - Routes are registered!")
    if isinstance(result.get("response"), dict):
        print(f"   Response: {result['response'].get('message', 'N/A')}")
else:
    print(f"   ❌ {result.get('status', 'ERROR')} - Routes NOT registered")
    if result.get("status") == 404:
        print("   ⚠️  This means the route doesn't exist - code might not be deployed")

# Test 5: Process Singlish endpoint (the main one)
print("\n5. Testing process-singlish endpoint...")
test_data = {
    "user_id": "render_test",
    "transcript": "walao this uncle cut queue sia"
}
result = test_endpoint(
    "Process Singlish",
    "POST",
    "/api/orchestrator/process-singlish",
    expected_status=200,
    data=test_data
)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - Endpoint works!")
    if isinstance(result.get("response"), dict):
        print(f"   Original: {result['response'].get('singlish_raw', 'N/A')}")
        print(f"   English:  {result['response'].get('clean_english', 'N/A')}")
        print(f"   Sentiment: {result['response'].get('sentiment', 'N/A')}")
else:
    status = result.get("status")
    if status == 404:
        print(f"   ❌ 404 - Endpoint NOT FOUND")
        print("   ⚠️  Route is not registered. Check:")
        print("      - Is code actually deployed?")
        print("      - Check Render logs for import errors")
        print("      - Force manual redeploy")
    elif status == 500:
        print(f"   ❌ 500 - Server error")
        if isinstance(result.get("response"), dict):
            error = result["response"].get("detail", "Unknown error")
            print(f"   Error: {error}")
            if "OPENAI_API_KEY" in error:
                print("   ⚠️  OpenAI API key not set in Render environment")
    else:
        print(f"   ❌ {status} - {result.get('error', 'Request failed')}")

# Test 6: Check API docs
print("\n6. Testing API docs endpoint...")
result = test_endpoint("API Docs", "GET", "/docs", expected_status=200)
results["tests"].append(result)
if result["success"]:
    print(f"   ✅ {result['status']} - API docs accessible")
    # Check if process-singlish is mentioned in docs
    if isinstance(result.get("response"), str) and "process-singlish" in result["response"]:
        print("   ✅ process-singlish endpoint found in docs")
    else:
        print("   ⚠️  process-singlish not found in docs (might be normal)")
else:
    print(f"   ❌ {result.get('status', 'ERROR')} - API docs not accessible")

# Summary
print(f"\n{'='*70}")
print("TEST SUMMARY")
print(f"{'='*70}\n")

passed = sum(1 for t in results["tests"] if t.get("success"))
total = len(results["tests"])

for test in results["tests"]:
    status_icon = "✅" if test.get("success") else "❌"
    status_code = test.get("status", "N/A")
    name = test.get("name", "Unknown")
    print(f"{status_icon} {name}: {status_code}")

print(f"\nResults: {passed}/{total} tests passed")

# Diagnosis
print(f"\n{'='*70}")
print("DIAGNOSIS")
print(f"{'='*70}\n")

test_route_result = next((t for t in results["tests"] if t.get("name") == "Test Route"), None)
singlish_result = next((t for t in results["tests"] if t.get("name") == "Process Singlish"), None)

if test_route_result and test_route_result.get("status") == 404:
    print("🔴 CRITICAL: Routes are NOT being registered")
    print("\nPossible causes:")
    print("  1. Code not actually deployed (force redeploy)")
    print("  2. Import error during startup (check Render runtime logs)")
    print("  3. Missing dependencies (check Render build logs)")
    print("\nAction: Check Render Runtime Logs for errors")
    
elif singlish_result and singlish_result.get("status") == 404:
    print("🟡 WARNING: process-singlish endpoint not found")
    if test_route_result and test_route_result.get("success"):
        print("  But other routes work - issue is specific to this endpoint")
        print("\nPossible causes:")
        print("  1. Route definition has an error")
        print("  2. Route not included in router properly")
        print("\nAction: Check app/orchestrator/routes.py for syntax errors")
    else:
        print("  And other routes also fail - routes not registering")
        
elif singlish_result and singlish_result.get("status") == 500:
    print("🟡 WARNING: Endpoint exists but returns 500 error")
    print("\nPossible causes:")
    print("  1. OPENAI_API_KEY not set in Render environment")
    print("  2. OpenAI API error")
    print("  3. Code error in endpoint handler")
    print("\nAction: Check Render Runtime Logs for error details")
    
elif singlish_result and singlish_result.get("success"):
    print("🟢 SUCCESS: Everything is working!")
    print("  The endpoint is deployed and functioning correctly.")
    
else:
    print("🟡 UNKNOWN: Could not determine issue")
    print("  Check individual test results above")

# Save results
with open("render_test_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*70}")
print(f"Results saved to: render_test_results.json")
print(f"{'='*70}\n")

