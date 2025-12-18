"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import BellbankHelper

BellbankBlueprint = Blueprint("bellbank", __name__)

BellbankBlueprint.route("/bellbank/webhook",
                        methods=['POST'])(jwt_required(BellbankHelper.bellbank_webhook))
#
