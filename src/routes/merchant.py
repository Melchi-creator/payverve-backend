"""
merchant.py

Routes for registering a shop and reading its profile.
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import MerchantResource, MerchantSettingsResource

MerchantBlueprint = Blueprint("merchant", __name__)

MerchantBlueprint.route("/merchants", methods=['POST'])(
    jwt_required(MerchantResource.create))
MerchantBlueprint.route("/merchants/me", methods=['GET'])(
    jwt_required(MerchantResource.read_mine))

# Owner-only, and each needs the owner's transaction pin in the body.
MerchantBlueprint.route("/merchants/me/secret-key", methods=['POST'])(
    jwt_required(MerchantSettingsResource.rotate_secret_key))
MerchantBlueprint.route("/merchants/me/webhook-secret", methods=['POST'])(
    jwt_required(MerchantSettingsResource.rotate_webhook_secret))
MerchantBlueprint.route("/merchants/me/webhook", methods=['PUT'])(
    jwt_required(MerchantSettingsResource.update_webhook_url))
