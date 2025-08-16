"""
swap_currency.py

Defines all api routes for swapped currencies resources especially CRUD
"""

from flask import Blueprint

from ..middlewares import jwt_required
from ..resources import SwapCurrencyResource

SwapCurrencyBlueprint = Blueprint("swap_currency", __name__)

SwapCurrencyBlueprint.route("/swap-currencies", methods=['POST'])(jwt_required(SwapCurrencyResource.create))
SwapCurrencyBlueprint.route("/swap-currencies", methods=['GET'])(jwt_required(SwapCurrencyResource.read_all))
SwapCurrencyBlueprint.route("/swap-currencies/<uuid:id>", methods=['GET'])(jwt_required(SwapCurrencyResource.read_one))
