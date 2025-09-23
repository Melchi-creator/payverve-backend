"""
payverve_transfer.py

Defines all api routes for payverve transfer resources especially CRUD
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import PayverveTransferResource

PayverveTransferBlueprint = Blueprint("payverve_transfer", __name__)

PayverveTransferBlueprint.route("/payverve-transfers", methods=['POST'])(jwt_required(PayverveTransferResource.create))
PayverveTransferBlueprint.route("/payverve-transfers", methods=['GET'])(jwt_required(PayverveTransferResource.read_all))
PayverveTransferBlueprint.route("/payverve-transfers/<uuid:id>", methods=['GET'])(jwt_required(PayverveTransferResource.read_one))
