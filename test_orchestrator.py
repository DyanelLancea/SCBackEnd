"""
Test script for Orchestrator Agent
Tests audio transcription + Singlish → English translation
"""

import requests
import json
import os
import sys

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Base URL - configurable via environment variable or command line
DEFAULT_URL = "http://localhost:8000"

# Check for custom backend URL
if len(sys.argv) > 1:
    BACKEND_URL = sys.argv[1].rstrip('/')
elif os.getenv("BACKEND_URL"):
    BACKEND_URL = os.getenv("BACKEND_URL").rstrip('/')
else:
    BACKEND_URL = DEFAULT_URL

BASE_URL = f"{BACKEND_URL}/api/orchestrator"


def test_info():
    """Test the info endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Get Orchestrator Info")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def test_quick_test():
    """Test the built-in test endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Quick Test Endpoint")
    print("="*60)
    
    response = requests.post(f"{BASE_URL}/test")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))


def test_process_text():
    """Test text processing"""
    print("\n" + "="*60)
    print("TEST 3: Process Text (Singlish → English)")
    print("="*60)
    
    test_cases = [
        "walao this uncle cut queue sia",
        "aiyah why you so like that one",
        "eh bro you free this weekend anot?",
        "wah lau this queue damn long leh",
        "can lah no problem one"
    ]
    
    for transcript in test_cases:
        print(f"\n📝 Input: '{transcript}'")
        
        response = requests.post(
            f"{BASE_URL}/process/text",
            json={"transcript": transcript}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Clean English: {result['clean_english']}")
            print(f"   Sentiment: {result['sentiment']}")
            print(f"   Tone: {result['tone']}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)


def test_process_with_form():
    """Test form-based processing (same as audio upload)"""
    print("\n" + "="*60)
    print("TEST 4: Process with Form Data (transcript only)")
    print("="*60)
    
    transcript = "wah lau eh this one really too much liao"
    
    response = requests.post(
        f"{BASE_URL}/process",
        data={"transcript": transcript}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Result:")
        print(json.dumps(result, indent=2))
    else:
        print(f"❌ Error: {response.text}")


def test_audio_upload():
    """Test audio file upload (requires actual audio file)"""
    print("\n" + "="*60)
    print("TEST 5: Audio Upload (Demo)")
    print("="*60)
    
    print("To test audio upload:")
    print("1. Record an audio file (mp3, wav, m4a)")
    print("2. Use the following code:")
    print("""
import requests

with open("your_audio.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/orchestrator/process",
        files={"audio": ("audio.mp3", f, "audio/mpeg")}
    )
    print(response.json())
""")
    print("\n⚠️  Skipping actual audio test (no audio file provided)")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 ORCHESTRATOR AGENT TEST SUITE")
    print("="*60)
    print("Testing Whisper STT + Singlish → English translation")
    print(f"Backend URL: {BACKEND_URL}")
    print("="*60)
    
    try:
        # Test 1: Info endpoint
        test_info()
        
        # Test 2: Quick test
        test_quick_test()
        
        # Test 3: Process multiple text examples
        test_process_text()
        
        # Test 4: Form data processing
        test_process_with_form()
        
        # Test 5: Audio upload demo
        test_audio_upload()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to backend")
        print(f"   Backend URL: {BACKEND_URL}")
        print("\n   For local backend:")
        print("     python -m app.main")
        print("     Or use: ./start.bat (Windows) or ./start.sh (Linux/Mac)")
        print("\n   For remote backend:")
        print(f"     python test_orchestrator.py https://your-backend-url.com")
        print(f"     Or set BACKEND_URL environment variable")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    # Show usage info if --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("\nUsage:")
        print("  python test_orchestrator.py [BACKEND_URL]")
        print("\nExamples:")
        print("  # Test local backend")
        print("  python test_orchestrator.py")
        print("  python test_orchestrator.py http://localhost:8000")
        print("\n  # Test remote backend")
        print("  python test_orchestrator.py https://scbackend-qfh6.onrender.com")
        print("\n  # Use environment variable")
        print("  set BACKEND_URL=https://scbackend-qfh6.onrender.com")
        print("  python test_orchestrator.py")
        sys.exit(0)
    
    main()

