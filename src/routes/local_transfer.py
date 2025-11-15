"""
local_currency.py

Defines all api routes for local currencies resources especially CRUD
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import LocalTransferResource

LocalTransferBlueprint = Blueprint("local_transfer", __name__)

LocalTransferBlueprint.route("/local-transfers/find-account", methods=['POST'])(jwt_required(LocalTransferResource.resolve_account))
LocalTransferBlueprint.route("/local-transfers", methods=['POST'])(jwt_required(LocalTransferResource.create))
LocalTransferBlueprint.route("/local-transfers", methods=['GET'])(jwt_required(LocalTransferResource.read_all))
LocalTransferBlueprint.route("/local-transfers/<uuid:id>", methods=['GET'])(jwt_required(LocalTransferResource.read_one))
LocalTransferBlueprint.route("/local-transfers/user/<uuid:id>", methods=['GET'])(jwt_required(LocalTransferResource.user_ltf_all))
