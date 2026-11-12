"""
src/routes/payverve_wallet.py
This module defines the PayverveWalletBlueprint, which sets up a route for retrieving all Payverve wallet funds.
It imports the necessary Flask components and the PayverveWalletResource class to handle the request.
"""
from flask import Blueprint

from src.auth import admin_required, jwt_required
from src.resources import PayverveWalletResource

# This is Payverve's own float, decrypted, and it was world-readable.
PayverveWalletBlueprint = Blueprint("payverve_wallet", __name__)

PayverveWalletBlueprint.route("/payverve-wallets", methods=['GET'])(jwt_required(admin_required(PayverveWalletResource.read)))