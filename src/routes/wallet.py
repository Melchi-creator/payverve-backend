"""
wallet.py

Defines all api routes for wallets resources especially CRUD
"""

from flask import Blueprint

from ..resources import WalletResource

WalletBlueprint = Blueprint("wallet", __name__)

WalletBlueprint.route("/wallets", methods=['POST'])(WalletResource.create)
WalletBlueprint.route("/wallets", methods=['GET'])(WalletResource.read_all)
WalletBlueprint.route("/wallets/<uuid:id>", methods=['GET'])(WalletResource.read_one)
WalletBlueprint.route("/wallets/<uuid:id>", methods=['PUT'])(WalletResource.update)
WalletBlueprint.route("/wallets/<uuid:id>", methods=['DELETE'])(WalletResource.delete)
