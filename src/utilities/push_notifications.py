"""
src/utilities/push_notifications.py
Sends push notifications to devices via Firebase Cloud Messaging (FCM),
using the Firebase Admin SDK.
"""

import firebase_admin
from firebase_admin import credentials, messaging

import config

_firebase_app = None


def _get_firebase_app():
    """Lazily initializes the Firebase Admin app exactly once."""
    global _firebase_app
    if _firebase_app is None:
        cred = credentials.Certificate(config.firebase_service_account_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    """
    Sends a push notification to a single device via its FCM token.
    Returns True on success, False on failure (never raises, to avoid
    breaking whatever calling flow triggered the notification).
    """
    if not fcm_token:
        return False

    try:
        _get_firebase_app()

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
        )

        response = messaging.send(message)
        print(f"Push notification sent: {response}")
        return True

    except Exception as e:
        print(f"Failed to send push notification: {e}")
        return False
