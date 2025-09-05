"""
src/routes/exchange_rate.py
This module defines the routes for managing exchange rates.
It includes a route for creating exchange rates, protected by JWT authentication.
"""

from flask import Blueprint

from ..auth import jwt_required
from ..middlewares import ExchangeRate

from ..resources import ExchangeRateResource

ExchangeRateBlueprint = Blueprint("exchange_rate", __name__)

ExchangeRateBlueprint.route("/exchange-rates-api", methods=['POST'])(jwt_required(ExchangeRate.exchange_pair))
ExchangeRateBlueprint.route("/exchange-rates", methods=['POST'])(jwt_required(ExchangeRateResource.create))
ExchangeRateBlueprint.route("/exchange-rates", methods=['GET'])(jwt_required(ExchangeRateResource.read_all))
ExchangeRateBlueprint.route("/exchange-rates/<uuid:id>", methods=['GET'])(jwt_required(ExchangeRateResource.read_one))
ExchangeRateBlueprint.route("/exchange-rates/<string:base_currency>/<string:target_currency>", methods=['GET'])(jwt_required(ExchangeRateResource.read_pair_today))
ExchangeRateBlueprint.route("/exchange-rates/all/<string:base_currency>/<string:target_currency>", methods=['GET'])(jwt_required(ExchangeRateResource.read_pair_all))
