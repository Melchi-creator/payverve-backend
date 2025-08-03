"""
src/routes/wallet.py
This module defines the WalletBlueprint for wallet-related routes in the Flask application.
It includes routes for creating, reading, and managing wallets.
"""

from flask import Blueprint

from ..middlewares import jwt_required
from ..resources import WalletResource

WalletBlueprint = Blueprint("wallet", __name__)

WalletBlueprint.route("/wallets", methods=['POST'])(jwt_required(WalletResource.create))
WalletBlueprint.route("/wallets", methods=['GET'])(jwt_required(WalletResource.read_all))
WalletBlueprint.route("/wallets/<uuid:id>", methods=['GET'])(jwt_required(WalletResource.read_one))
WalletBlueprint.route("/wallets/user/<uuid:id>", methods=['GET'])(jwt_required(WalletResource.read_all_user))
WalletBlueprint.route("/wallets/<uuid:id>", methods=['PUT'])(jwt_required(WalletResource.update))
