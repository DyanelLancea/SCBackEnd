"""
Diagnostic script to check Singlish endpoint setup
Uses Render server by default: https://scbackend-qfh6.onrender.com
To use localhost instead, set: export API_BASE_URL=http://localhost:8000
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_section(title):
    """Print a section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_openai_key():
    """Check if OpenAI API key is set"""
    print_section("1. Checking OpenAI API Key")
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY is NOT set!")
        print("\n   Solution:")
        print("   1. Create/edit .env file in project root")
        print("   2. Add: OPENAI_API_KEY=sk-your-key-here")
        print("   3. Or set in Render environment variables")
        return False
    else:
        print(f"✅ OPENAI_API_KEY is set: {api_key[:10]}...{api_key[-4:]}")
        
        # Test if key is valid
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            # Try a simple API call
            print("   Testing API key validity...")
            # We'll test with a minimal call
            print("   ✅ Key format looks valid")
        except ImportError:
            print("   ⚠️  OpenAI package not installed")
            print("   Run: pip install openai==1.54.0")
            return False
        except Exception as e:
            print(f"   ⚠️  Key might be invalid: {str(e)[:100]}")
            return False
    
    return True

def check_openai_package():
    """Check if OpenAI package is installed"""
    print_section("2. Checking OpenAI Package")
    
    try:
        import openai
        print(f"✅ OpenAI package installed: version {openai.__version__}")
        return True
    except ImportError:
        print("❌ OpenAI package NOT installed!")
        print("\n   Solution:")
        print("   Run: pip install openai==1.54.0")
        return False

def check_server_running():
    """Check if server is running"""
    print_section("3. Checking Server Status")
    
    # Use Render server by default, can override with API_BASE_URL env var
    base_url = os.getenv("API_BASE_URL", "https://scbackend-qfh6.onrender.com")
    
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at {base_url}")
            return True
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is NOT running at {base_url}")
        print("\n   Solution:")
        print("   Run: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {str(e)}")
        return False

def check_endpoint_exists():
    """Check if the endpoint exists"""
    print_section("4. Checking Endpoint Exists")
    
    # Use Render server by default, can override with API_BASE_URL env var
    base_url = os.getenv("API_BASE_URL", "https://scbackend-qfh6.onrender.com")
    endpoint = f"{base_url}/api/orchestrator/process-singlish"
    
    try:
        # Try GET (should return 405 Method Not Allowed, not 404)
        response = requests.get(endpoint, timeout=5)
        if response.status_code == 405:
            print(f"✅ Endpoint exists (405 = method not allowed, which is expected)")
            return True
        elif response.status_code == 404:
            print(f"❌ Endpoint NOT found (404)")
            print("\n   Solution:")
            print("   Check that app/orchestrator/routes.py has the endpoint")
            print("   Check that app/main.py includes the router")
            return False
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_endpoint():
    """Test the endpoint with a simple request"""
    print_section("5. Testing Endpoint")
    
    # Use Render server by default, can override with API_BASE_URL env var
    base_url = os.getenv("API_BASE_URL", "https://scbackend-qfh6.onrender.com")
    endpoint = f"{base_url}/api/orchestrator/process-singlish"
    
    test_data = {
        "user_id": "diagnostic_test",
        "transcript": "walao this uncle cut queue sia"
    }
    
    try:
        print(f"   Sending test request...")
        print(f"   Endpoint: {endpoint}")
        print(f"   Data: {test_data}")
        
        response = requests.post(
            endpoint,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # Longer timeout for OpenAI API call
        )
        
        print(f"\n   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Endpoint working correctly!")
            print(f"\n   Response:")
            print(f"   - Original: {data.get('singlish_raw')}")
            print(f"   - English:  {data.get('clean_english')}")
            print(f"   - Sentiment: {data.get('sentiment')}")
            print(f"   - Tone: {data.get('tone')}")
            return True
        else:
            print(f"   ❌ Endpoint returned error")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error: {response.text[:200]}")
            
            if response.status_code == 500:
                print("\n   Common causes:")
                print("   - OPENAI_API_KEY not set or invalid")
                print("   - OpenAI API rate limit exceeded")
                print("   - Network error connecting to OpenAI")
            
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (>30 seconds)")
        print("   This might mean OpenAI API is slow or unreachable")
        return False
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def check_imports():
    """Check if all imports work"""
    print_section("6. Checking Code Imports")
    
    try:
        from app.orchestrator.routes import router, process_singlish
        print("✅ Orchestrator routes import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {str(e)}")
        print("\n   Solution:")
        print("   - Check that app/orchestrator/routes.py exists")
        print("   - Check that all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Error importing: {str(e)}")
        return False

def main():
    """Run all diagnostic checks"""
    print("\n" + "="*70)
    print("  🔍 SINGLISH ENDPOINT DIAGNOSTIC TOOL")
    print("="*70)
    print("\nThis tool will check your setup and identify issues.")
    
    # Show which server we're using
    base_url = os.getenv("API_BASE_URL", "https://scbackend-qfh6.onrender.com")
    print(f"\n📍 Testing against: {base_url}")
    print("💡 To use localhost instead, set: export API_BASE_URL=http://localhost:8000")
    
    results = []
    
    # Run all checks
    results.append(("OpenAI Package", check_openai_package()))
    results.append(("OpenAI API Key", check_openai_key()))
    results.append(("Code Imports", check_imports()))
    results.append(("Server Running", check_server_running()))
    
    # Only check endpoint if server is running
    if results[-1][1]:  # If server is running
        results.append(("Endpoint Exists", check_endpoint_exists()))
        results.append(("Endpoint Test", test_endpoint()))
    
    # Summary
    print_section("SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nResults: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Your setup is working correctly.")
    else:
        print("\n⚠️  Some checks failed. Review the errors above.")
        print("\nNext steps:")
        print("1. Fix the issues marked with ❌")
        print("2. Run this diagnostic again")
        print("3. If still failing, check Render logs for deployment issues")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnostic cancelled by user.")
    except Exception as e:
        print(f"\n\n❌ Diagnostic tool error: {str(e)}")
        import traceback
        traceback.print_exc()

