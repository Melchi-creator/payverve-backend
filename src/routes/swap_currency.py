"""
swap_currency.py

Defines all api routes for exchange rate resources especially CRUD
"""

from flask import Blueprint

from ..resources import SwapCurrencyResource

SwapCurrencyBlueprint = Blueprint("swap_currency", __name__)

SwapCurrencyBlueprint.route("/swap-currencies", methods=['POST'])(SwapCurrencyResource.create)
SwapCurrencyBlueprint.route("/swap-currencies", methods=['GET'])(SwapCurrencyResource.read_all)
SwapCurrencyBlueprint.route("/swap-currencies/<uuid:id>", methods=['GET'])(SwapCurrencyResource.read_one)
SwapCurrencyBlueprint.route("/swap-currencies/<uuid:id>", methods=['DELETE'])(SwapCurrencyResource.delete)
