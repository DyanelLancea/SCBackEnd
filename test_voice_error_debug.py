"""
Debug script to test voice endpoint and identify the exact error
"""

import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

async def test_voice_endpoint():
    """Test the voice endpoint with a simple transcript"""
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    url = f"{base_url}/api/orchestrator/voice"
    
    # Test with a simple transcript
    payload = {
        "user_id": "test-user-123",
        "transcript": "Hello, I need help",
        "location": "Test Location"
    }
    
    print(f"Testing voice endpoint: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()
            
            try:
                response_data = response.json()
                print(f"Response JSON:")
                print(json.dumps(response_data, indent=2))
            except Exception as e:
                print(f"Response Text: {response.text}")
                print(f"Could not parse JSON: {e}")
            
            if response.status_code != 200:
                print(f"\n❌ Error: Status code {response.status_code}")
                if response.headers.get("content-type", "").startswith("application/json"):
                    error_detail = response_data.get("detail", "Unknown error")
                    print(f"Error Detail: {error_detail}")
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_voice_endpoint())


