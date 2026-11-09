"""
merchant.py

Routes for registering a shop and reading its profile.
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import MerchantResource

MerchantBlueprint = Blueprint("merchant", __name__)

MerchantBlueprint.route("/merchants", methods=['POST'])(
    jwt_required(MerchantResource.create))
MerchantBlueprint.route("/merchants/me", methods=['GET'])(
    jwt_required(MerchantResource.read_mine))
