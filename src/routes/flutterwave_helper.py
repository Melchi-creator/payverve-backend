"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import FltterwaveHelper

FlutterwaveBlueprint = Blueprint("flutterwave", __name__)

FlutterwaveBlueprint.route("/flutterwave-create-ngn",
                           methods=['POST'])(jwt_required(FltterwaveHelper.flutterwave_create_vna))

FlutterwaveBlueprint.route("/list-of-banks", methods=['GET'])(jwt_required(FltterwaveHelper.flutterwave_list_of_banks))

FlutterwaveBlueprint.route("/payverve-flw-webhooks", methods=['GET'])(FltterwaveHelper.flutterwave_webhook)
