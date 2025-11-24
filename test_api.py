#!/usr/bin/env python
"""
Quick test script to verify the REST API endpoint is working.
Run this while your Django server is running.
"""

import requests
import json

API_URL = "http://127.0.0.1:8000/api/chat/messages/"

print("Testing REST API endpoint...")
print(f"URL: {API_URL}\n")

# Test GET
print("1. Testing GET request...")
try:
    response = requests.get(API_URL)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    print("   ✓ GET request successful\n")
except Exception as e:
    print(f"   ✗ GET request failed: {e}\n")

# Test POST
print("2. Testing POST request...")
try:
    payload = {
        "sender_username": "testuser",
        "text": "Test message from API test script"
    }
    response = requests.post(
        API_URL,
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print("   ✓ POST request successful\n")
    else:
        print(f"   Error: {response.text}")
        print("   ✗ POST request failed\n")
except Exception as e:
    print(f"   ✗ POST request failed: {e}\n")

# Test GET again to see the new message
print("3. Testing GET request again (should show new message)...")
try:
    response = requests.get(API_URL)
    print(f"   Status: {response.status_code}")
    messages = response.json()
    print(f"   Found {len(messages)} message(s)")
    if messages:
        print(f"   Latest message: {messages[-1]}")
    print("   ✓ GET request successful\n")
except Exception as e:
    print(f"   ✗ GET request failed: {e}\n")

print("Test complete!")


