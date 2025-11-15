"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import FlutterwaveHelper

FlutterwaveBlueprint = Blueprint("flutterwave", __name__)

# FlutterwaveBlueprint.route("/flutterwave-create-ngn",
#                            methods=['POST'])(jwt_required(FlutterwaveHelper.flutterwave_create_vna))
#
# FlutterwaveBlueprint.route("/payverve-flw-webhooks", methods=['GET'])(FlutterwaveHelper.flutterwave_webhook)
