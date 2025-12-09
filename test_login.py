import requests
import json

url = 'http://localhost:8000/api/chat/users/'
data = {
    "username": "testuser_debug",
    "first_name": "Test Debug",
    "phone_number": "1234567890"
}
headers = {'Content-Type': 'application/json'}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
