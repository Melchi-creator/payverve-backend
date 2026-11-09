"""
charge.py

Routes for charges and the buyer-facing checkout.

Three different authentications, deliberately:

  /charges            merchant_required  the shop's server, by secret key
  /checkout/<code>    none               the buyer, who has no session yet
  .../pay-with-wallet jwt_required       the buyer, signed in to Payverve
"""

from flask import Blueprint

from ..auth import jwt_required
from ..auth.merchant_auth import merchant_required
from ..resources import ChargeResource, CheckoutResource

ChargeBlueprint = Blueprint("charge", __name__)

# Shop server. Authenticated by secret key, never by a Payverve session.
ChargeBlueprint.route("/charges", methods=['POST'])(
    merchant_required(ChargeResource.create))
ChargeBlueprint.route("/charges/<string:reference>", methods=['GET'])(
    merchant_required(ChargeResource.verify))

# Buyer's browser, arriving from the shop with no Payverve session. The
# charge_code is the credential: unguessable, and it reveals only this one
# charge.
ChargeBlueprint.route("/checkout/<string:charge_code>", methods=['GET'])(
    CheckoutResource.read)

# Buyer paying from their Payverve balance, signed in.
ChargeBlueprint.route("/checkout/<string:charge_code>/pay-with-wallet",
                      methods=['POST'])(
    jwt_required(CheckoutResource.pay_with_wallet))
