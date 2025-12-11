"""
Test SOS endpoint to verify it's accessible
"""

import httpx
import asyncio
import json

async def test_sos_endpoint():
    """Test the SOS endpoint"""
    base_url = "https://scbackend-qfh6.onrender.com"
    url = f"{base_url}/api/safety/sos"
    
    payload = {
        "user_id": "test-user-123",
        "location": "Test Location",
        "message": "Test SOS call"
    }
    
    print(f"Testing SOS endpoint: {url}")
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
                print(f"Response Text: {response.text[:500]}")
                print(f"Could not parse JSON: {e}")
            
            if response.status_code == 200:
                print("\n✅ SOS endpoint is accessible and working!")
            else:
                print(f"\n⚠️ SOS endpoint returned status {response.status_code}")
                
    except httpx.TimeoutException:
        print("❌ Request timed out - backend might be slow or unreachable")
    except httpx.ConnectError as e:
        print(f"❌ Connection error - backend is not reachable: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sos_endpoint())

