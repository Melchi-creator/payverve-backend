"""

"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import ForeignTransferResource

ForeignTransferBlueprint = Blueprint("foreign_transfer", __name__)

ForeignTransferBlueprint.route("/foreign-transfers/find-account", methods=['POST'])(jwt_required(ForeignTransferResource.resolve_account))
ForeignTransferBlueprint.route("/foreign-transfers", methods=['POST'])(jwt_required(ForeignTransferResource.create))
ForeignTransferBlueprint.route("/foreign-transfers", methods=['GET'])(jwt_required(ForeignTransferResource.read_all))
ForeignTransferBlueprint.route("/foreign-transfers/<uuid:id>", methods=['GET'])(jwt_required(ForeignTransferResource.read_one))
ForeignTransferBlueprint.route("/foreign-transfers/user/<uuid:id>", methods=['GET'])(jwt_required(ForeignTransferResource.user_ftf_all))
