"""

"""

from flask import Blueprint

from ..resources import TokenVerification

TokenVerificationBlueprint = Blueprint("token_verification", __name__)

TokenVerificationBlueprint.route("/token-verifications", methods=['GET'])(TokenVerification.read)
