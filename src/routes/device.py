"""
src/routes/device.py
Routes for device-specific data, such as registering FCM tokens for push notifications.
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import DeviceResource

DeviceBlueprint = Blueprint("device", __name__)

DeviceBlueprint.route("/device/register-fcm-token",
                      methods=['POST'])(jwt_required(DeviceResource.register_fcm_token))
