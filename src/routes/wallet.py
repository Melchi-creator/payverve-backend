"""
src/routes/wallet.py
This module defines the WalletBlueprint for wallet-related routes in the Flask application.
It includes routes for creating, reading, and managing wallets.
"""

from flask import Blueprint

from ..auth import admin_required, jwt_required
from ..resources import WalletResource

WalletBlueprint = Blueprint("wallet", __name__)

# Unauthenticated, and vestigial: registration stages the NGN wallet in its
# own transaction now rather than calling this over HTTP. Left routed but
# behind a token, because creating a wallet for an arbitrary user_id is not
# something an anonymous caller should be able to do.
WalletBlueprint.route("/ngn-wallets", methods=['POST'])(
    jwt_required(WalletResource.ngn_create))
WalletBlueprint.route("/wallets", methods=['POST'])(jwt_required(WalletResource.other_wallet))
WalletBlueprint.route("/wallets", methods=['GET'])(jwt_required(WalletResource.read_all))
WalletBlueprint.route("/wallets/<uuid:id>", methods=['GET'])(jwt_required(WalletResource.read_one))
WalletBlueprint.route("/wallets/user/<uuid:id>", methods=['GET'])(jwt_required(WalletResource.read_all_user))
# This ADDS the posted amount to the wallet balance and saves. Behind
# jwt_required alone, with no ownership check, it let any signed-in
# customer credit any wallet -- their own included -- by any amount, out
# of nothing, and then move it out through /local-transfers. Ownership is
# not the fix: a customer must not be able to do this to their own wallet
# either. Balances move through deposits, transfers and swaps only.
WalletBlueprint.route("/wallets/<uuid:id>", methods=['PUT'])(
    jwt_required(admin_required(WalletResource.update)))
