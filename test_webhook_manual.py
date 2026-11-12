import hmac
import hashlib
import base64
import json
import secrets
import requests
import config

secret_hash = config.flutterwave_secret_hash

payload = {
    "webhook_id": "wbk_test_manual_003",
    "timestamp": 1748850422635,
    "type": "charge.completed",
    "data": {
        "id": f"chg_test_{secrets.token_hex(6)}",  # unique each run
        "amount": 175,
        "currency": "NGN",
        "status": "succeeded",
        "payment_method_details": {"type": "bank_transfer"},
        "reference": f"test-sim-ref-{secrets.token_hex(4)}",
        "customer": {"id": "cus_atqaxYyhTZ"}
    }
}

raw_body = json.dumps(payload).encode()

signature = base64.b64encode(
    hmac.new(secret_hash.encode(), raw_body, hashlib.sha256).digest()
).decode()

print("Testing with charge_id:", payload["data"]["id"])

response = requests.post(
    "http://localhost:5000/payverve-flw-webhooks",
    data=raw_body,
    headers={
        "Content-Type": "application/json",
        "flutterwave-signature": signature
    }
)

print(response.status_code)
print(response.text)
