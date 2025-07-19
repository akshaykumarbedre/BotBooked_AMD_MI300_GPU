import requests

SERVER_B_URL = "http://134.199.205.208:5000/receive"

try:
    response = requests.post(
        SERVER_B_URL,
        json={"message": "Test"},
        timeout=5  # 5-second timeout
    )
    print(f"✅ Success! Response: {response.json()}")
except requests.exceptions.Timeout:
    print("❌ Timeout: Server B didn't respond in time.")
except requests.exceptions.ConnectionError:
    print("❌ Connection Error: Is Server B running? Check IP/port/firewall.")
except Exception as e:
    print(f"❌ Error: {e}")