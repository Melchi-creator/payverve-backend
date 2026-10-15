"""

"""

from flask import Blueprint

from ..auth import admin_required, jwt_required
from ..resources import TokenVerification

TokenVerificationBlueprint = Blueprint("token_verification", __name__)

# Was world-readable with no auth at all, and returns code_sent plus the
# channel_contact it went to for every token, newest first. That is an
# unauthenticated account takeover: request a password reset for any
# address, read the OTP here, reset the password. Admins only.
TokenVerificationBlueprint.route("/token-verifications", methods=['GET'])(
    jwt_required(admin_required(TokenVerification.read)))
