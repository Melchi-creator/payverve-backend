"""
src/routes/payverve_wallet.py
This module defines the PayverveWalletBlueprint, which sets up a route for retrieving all Payverve wallet funds.
It imports the necessary Flask components and the PayverveWalletResource class to handle the request.
"""
from flask import Blueprint

from src.resources import PayverveWalletResource

PayverveWalletBlueprint = Blueprint("payverve_wallet", __name__)

PayverveWalletBlueprint.route("/payverve-wallets", methods=['GET'])(PayverveWalletResource.read)