"""
test_push.py
One-off script to test Firebase push notification delivery,
decoupled from the Flutterwave webhook flow.
Run with: python test_push.py
"""

from server import server
from src.models import UserModel
from src.utilities.push_notifications import send_push_notification

TEST_USER_EMAIL = "edwardaja66@gmail.com"  # adjust if needed

with server.app_context():
    user = UserModel.query.filter_by(email_address=TEST_USER_EMAIL).first()

    if not user:
        print(f"No user found with email {TEST_USER_EMAIL}")
    elif not user.fcm_token:
        print(f"User {TEST_USER_EMAIL} has no fcm_token stored.")
    else:
        print(f"Sending test push to token: {user.fcm_token[:20]}...")
        success = send_push_notification(
            fcm_token=user.fcm_token,
            title="Test Notification",
            body="If you see this, Firebase Admin SDK is working!",
            data={"type": "test"},
        )
        print(f"Success: {success}")
