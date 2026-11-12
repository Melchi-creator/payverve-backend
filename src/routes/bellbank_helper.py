"""

"""

from flask import Blueprint

from ..middlewares import BellbankHelper

BellbankBlueprint = Blueprint("bellbank", __name__)

# NOTE: deliberately NOT jwt_required.
#
# BellBank is a third party calling us; it has no Payverve JWT to present, so
# jwt_required returned 401 to every collection notification and no deposit was
# ever credited.
#
# The endpoint is authenticated instead by verifying BellBank's signature over
# the raw body inside BellbankHelper.verify_bellbank_signature, which fails
# closed. Do not add jwt_required back.
BellbankBlueprint.route("/bellbank/webhook",
                        methods=['POST'])(BellbankHelper.bellbank_webhook)
