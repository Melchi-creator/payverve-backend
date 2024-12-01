"""
payverve_transfer.py

Defines all api routes for payverve transfer resources especially CRUD
"""

from flask import Blueprint

from ..resources import PayverveTransferResource

PayverveTransferBlueprint = Blueprint("payverve_transfer", __name__)

PayverveTransferBlueprint.route("/payverve-transfers", methods=['POST'])(PayverveTransferResource.create)
PayverveTransferBlueprint.route("/payverve-transfers", methods=['GET'])(PayverveTransferResource.read_all)
PayverveTransferBlueprint.route("/payverve-transfers/<uuid:id>", methods=['GET'])(PayverveTransferResource.read_one)
# PayverveTransferBlueprint.route("/payverve-transfers/<uuid:id>", methods=['DELETE'])(PayverveTransferResource.delete)
