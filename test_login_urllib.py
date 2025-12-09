import json
import urllib.request
import urllib.error

url = 'http://localhost:8000/api/chat/users/'
data = {
    "username": "testuser_urllib",
    "first_name": "Test Urllib",
    "phone_number": "9876543210"
}
headers = {'Content-Type': 'application/json'}

try:
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
    with urllib.request.urlopen(req) as response:
        print(f"Status Code: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    content = e.read().decode('utf-8')
    with open('error.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Error content saved to error.html")
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
except Exception as e:
    print(f"General Error: {e}")
