#!/usr/bin/env python3
"""
Test script to verify the TypeError fixes
"""

import requests
import time
import subprocess
import sys
from threading import Thread

def start_server():
    """Start the FastAPI server in background"""
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app.main:app", "--host", "127.0.0.1", "--port", "8000"
    ])

def test_endpoints():
    """Test the endpoints that were causing issues"""
    base_url = "http://127.0.0.1:8000"
    
    # Wait for server to start
    print("Waiting for server to start...")
    time.sleep(3)
    
    try:
        # Test root endpoint
        print("Testing root endpoint...")
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
        
        # Test 404 error handler
        print("Testing 404 error handler...")
        response = requests.get(f"{base_url}/nonexistent")
        print(f"404 handler: {response.status_code}")
        
        # Test safety SOS endpoint (should return 422 for missing data, not 500)
        print("Testing safety SOS endpoint...")
        response = requests.post(f"{base_url}/api/safety/sos", json={})
        print(f"SOS endpoint: {response.status_code}")
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Make sure it's running.")
    except Exception as e:
        print(f"Test error: {e}")

if __name__ == "__main__":
    print("Starting test...")
    
    # Start server in background thread
    server_thread = Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Run tests
    test_endpoints()