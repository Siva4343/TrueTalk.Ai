import requests
import random

TWO_FACTOR_API_KEY = "76b005d0-c30a-11f0-a6b2-0200cd936042"

def send_otp(phone):
    url = f"https://2factor.in/API/V1/{TWO_FACTOR_API_KEY}/SMS/{phone}/AUTOGEN"
    
    response = requests.get(url)
    print("2Factor SMS Response:", response.text)

    data = response.json()

    if data.get("Status") != "Success":
        return "failed", "Failed to send OTP"

    # OTP is automatically sent by 2Factor; we store the session ID
    session_id = data.get("Details")
    return "success", session_id


def verify_otp(phone, otp, session_id):
    url = f"https://2factor.in/API/V1/{TWO_FACTOR_API_KEY}/SMS/VERIFY/{session_id}/{otp}"

    response = requests.get(url)
    print("Verify Response:", response.text)

    data = response.json()

    if data.get("Status") == "Success":
        return True
    return False
