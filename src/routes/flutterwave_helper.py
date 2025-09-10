"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import FltterwaveHelper

FlutterwaveyBlueprint = Blueprint("flutterwave", __name__)

FlutterwaveyBlueprint.route("/flutterwave-create-ngn",
                            methods=['POST'])(jwt_required(FltterwaveHelper.flutterwave_create_vna))
