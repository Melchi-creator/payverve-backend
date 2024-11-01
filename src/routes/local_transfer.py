"""
local_currency.py

Defines all api routes for local currencies resources especially CRUD
"""

from flask import Blueprint

from ..resources import LocalTransferResource

LocalTransferBlueprint = Blueprint("local_transfer", __name__)

LocalTransferBlueprint.route("/local_transfers", methods=['POST'])(LocalTransferResource.create)
LocalTransferBlueprint.route("/local_transfers", methods=['GET'])(LocalTransferResource.read_all)
LocalTransferBlueprint.route("/local_transfers/<uuid:id>", methods=['GET'])(LocalTransferResource.read_one)
# LocalTransferBlueprint.route("/local_transfers/<uuid:id>", methods=['DELETE'])(LocalTransferResource.delete)
