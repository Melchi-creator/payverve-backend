"""
src/routes/bank.py
Routes for bank listing and account number resolution.
"""

from flask import Blueprint

from ..auth import jwt_required
from ..resources import BankResource

BankBlueprint = Blueprint("bank", __name__)

BankBlueprint.route("/banks/<string:country>", methods=['GET']
                    )(jwt_required(BankResource.list_banks))
BankBlueprint.route("/banks/resolve-account", methods=['POST']
                    )(jwt_required(BankResource.resolve_account))
