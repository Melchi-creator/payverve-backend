"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import TargetSaveResource

TargetSaveBlueprint = Blueprint("target_savings", __name__)

TargetSaveBlueprint.route("/target-savings", methods=['POST'])(jwt_required(TargetSaveResource.create))
TargetSaveBlueprint.route("/target-savings", methods=['GET'])(jwt_required(TargetSaveResource.read))
TargetSaveBlueprint.route("/target-savings/<uuid:id>", methods=['GET'])(jwt_required(TargetSaveResource.fetch))
TargetSaveBlueprint.route("/target-savings/users/<uuid:id>",
                          methods=['GET'])(jwt_required(TargetSaveResource.fetch_user_ts))
TargetSaveBlueprint.route("/target-savings/break/<uuid:user_id>/<uuid:id>", methods=['PUT'])(jwt_required(
    TargetSaveResource.break_ts))
TargetSaveBlueprint.route("/target-savings/withdraw/<uuid:user_id>/<uuid:id>", methods=['POST'])(jwt_required(
    TargetSaveResource.withdraw_target_saving))
TargetSaveBlueprint.route("/target-savings/delete/<uuid:user_id>/<uuid:id>", methods=['DELETE'])(jwt_required(
    TargetSaveResource.delete_target_saving))
