"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import FixedDepositResource

FixedDepositBlueprint = Blueprint("fixed_deposits", __name__)

FixedDepositBlueprint.route("/fixed-deposits", methods=['POST'])(jwt_required(FixedDepositResource.create))
FixedDepositBlueprint.route("/fixed-deposits", methods=['GET'])(jwt_required(FixedDepositResource.read))
FixedDepositBlueprint.route("/fixed-deposits/<uuid:id>", methods=['GET'])(jwt_required(FixedDepositResource.fetch))
FixedDepositBlueprint.route("/fixed-deposits/users/<uuid:id>",
                          methods=['GET'])(jwt_required(FixedDepositResource.fetch_user_fd))
FixedDepositBlueprint.route("/fixed-deposits/withdraw/<uuid:user_id>/<uuid:id>", methods=['POST'])(jwt_required(
    FixedDepositResource.withdraw_fixed_deposit))

