"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import FlutterwaveHelper

FlutterwaveBlueprint = Blueprint("flutterwave", __name__)

FlutterwaveBlueprint.route("/payverve-flw-webhooks",
                           methods=['POST'])(FlutterwaveHelper.flutterwave_webhook)
