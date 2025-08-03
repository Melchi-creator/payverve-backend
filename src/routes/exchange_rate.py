"""
src/routes/exchange_rate.py
This module defines the routes for managing exchange rates.
It includes a route for creating exchange rates, protected by JWT authentication.
"""

from flask import Blueprint

from ..middlewares import ExchangeRate, jwt_required
from ..resources import ExchangeRateResource

ExchangeRateBlueprint = Blueprint("exchange_rate", __name__)

ExchangeRateBlueprint.route("/exchange-rates-api", methods=['POST'])(jwt_required(ExchangeRate.exchange_pair))
ExchangeRateBlueprint.route("/exchange-rates", methods=['POST'])(jwt_required(ExchangeRateResource.create))
ExchangeRateBlueprint.route("/exchange-rates", methods=['GET'])(jwt_required(ExchangeRateResource.read_all))
ExchangeRateBlueprint.route("/exchange-rates/<uuid:id>", methods=['GET'])(jwt_required(ExchangeRateResource.read_one))
