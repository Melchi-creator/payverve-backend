# check_customer.py
import hashlib
import hmac
import secrets
import requests

# --- Fill these in with your LIVE (production) values, not sandbox ---
# value of FLUTTERWAVE_AUTH_URL on Render
FLW_AUTH_URL = "https://idp.flutterwave.com"
# value of FLUTTERWAVE_BASE_URL on Render
FLW_BASE_URL = "https://f4bexperience.flutterwave.com"
# FLUTTERWAVE_CLIENT_ID on Render
FLW_CLIENT_ID = "e5eb0109-38dc-4ca6-8927-a647dda80ba5"
# FLUTTERWAVE_SECRET_KEY on Render
FLW_CLIENT_SECRET = "f1ha3STs7OEnrLNzLKgo4RvkayG7lS6q"
# SECRET_KEY on Render (for idempotency key)
SECRET_KEY = "2b41f9f6b5e428ed4bfcc031050f290aa7215c4de38e8999f5765f2c0f8c2b10"

EMAIL_TO_CHECK = "dikeaja66@gmail.com"

# 1. Authenticate
auth_response = requests.post(
    f"{FLW_AUTH_URL}/realms/flutterwave/protocol/openid-connect/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "client_id": FLW_CLIENT_ID,
        "client_secret": FLW_CLIENT_SECRET,
        "grant_type": "client_credentials",
    },
)
access_token = auth_response.json().get("access_token")
print("AUTH STATUS:", auth_response.status_code)

if not access_token:
    print("Could not authenticate — check your live credentials")
    exit()

# 2. Search for customer by email
idempotency_key = hmac.new(
    SECRET_KEY.encode(), EMAIL_TO_CHECK.encode(), hashlib.sha256
).hexdigest()

search_response = requests.post(
    f"{FLW_BASE_URL}/customers/search",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Trace-Id": secrets.token_urlsafe(12),
        "X-Idempotency-Key": idempotency_key,
    },
    json={"email": EMAIL_TO_CHECK},
)

# 3. List/check virtual accounts for this customer
va_response = requests.get(
    f"{FLW_BASE_URL}/virtual-accounts?customer_id=cus_jLiUTlv7Qn",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    },
)


# 4. Attempt to create the virtual account directly, capture full raw response

reference_number = "testref" + secrets.token_hex(6)
message = f"dikeaja66@gmail.com{0}NGN"
idempotency_key = hmac.new(
    SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

va_create_response = requests.post(
    f"{FLW_BASE_URL}/virtual-accounts",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Trace-Id": secrets.token_urlsafe(12),
        "X-Idempotency-Key": idempotency_key,
    },
    json={
        "reference": reference_number,
        "customer_id": "cus_jLiUTlv7Qn",
        "amount": 0,
        "currency": "NGN",
        "account_type": "static",
        "narration": "Payverve/Ogo Aja",
        "bank_code": "090772",
        "bvn": "22174600303",
    },
)


# Force a fresh idempotency key to bypass the cache
# add randomness to break the cache
message = f"dikeaja66@gmail.com{0}NGN{secrets.token_hex(4)}"
idempotency_key = hmac.new(
    SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

va_create_response2 = requests.post(
    f"{FLW_BASE_URL}/virtual-accounts",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Trace-Id": secrets.token_urlsafe(12),
        "X-Idempotency-Key": idempotency_key,
    },
    json={
        "reference": "testref" + secrets.token_hex(6),
        "customer_id": "cus_jLiUTlv7Qn",
        "amount": 0,
        "currency": "NGN",
        "account_type": "static",
        "narration": "Payverve/Ogo Aja",
        "bank_code": "090772",
        "bvn": "22174600303",
    },
)


test_email = "flwtest.obianujunwaedward@gmail.com"  # any unused email

message = f"{test_email}9034837062OgonnayaAjaNone"
idempotency_key = hmac.new(
    SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()

create_customer_response = requests.post(
    f"{FLW_BASE_URL}/customers",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Trace-Id": secrets.token_urlsafe(12),
        "X-Idempotency-Key": idempotency_key,
    },
    json={
        "email": test_email,
        "phone": {"country_code": "234", "number": "9034837062"},
        "name": {"first": "Test", "middle": None, "last": "Fresh"},
    },
)

# 6. Try virtual account creation against the BRAND NEW customer
message_new = f"flwtest.obianujunwaedward@gmail.com{0}NGN{secrets.token_hex(4)}"
idempotency_key_new = hmac.new(
    SECRET_KEY.encode(), message_new.encode(), hashlib.sha256).hexdigest()

va_new_customer_response = requests.post(
    f"{FLW_BASE_URL}/virtual-accounts",
    headers={
        "content-type": "application/json",
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "X-Trace-Id": secrets.token_urlsafe(12),
        "X-Idempotency-Key": idempotency_key_new,
    },
    json={
        "reference": "testref" + secrets.token_hex(6),
        "customer_id": "cus_KdgRoj0jO1",   # the NEW customer from this run
        "amount": 0,
        "currency": "NGN",
        "account_type": "static",
        "narration": "Payverve/Test Fresh",
        "bank_code": "090772",
        "bvn": "22174600303",
    },
)

print("VA FOR NEW CUSTOMER STATUS:", va_new_customer_response.status_code)
print("VA FOR NEW CUSTOMER BODY:", va_new_customer_response.text)

print("NEW CUSTOMER STATUS:", create_customer_response.status_code)
print("NEW CUSTOMER BODY:", create_customer_response.text)
print("FRESH CREATE VA STATUS:", va_create_response2.status_code)
print("FRESH CREATE VA HEADERS:", dict(va_create_response2.headers))
print("FRESH CREATE VA BODY:", va_create_response2.text)

print("CREATE VA STATUS:", va_create_response.status_code)
print("CREATE VA HEADERS:", dict(va_create_response.headers))
print("CREATE VA BODY:", va_create_response.text)
print("VA LIST STATUS:", va_response.status_code)
print("VA LIST BODY:", va_response.text)

print("SEARCH STATUS:", search_response.status_code)
print("SEARCH BODY:", search_response.text)
