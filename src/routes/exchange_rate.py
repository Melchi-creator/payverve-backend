"""
exchange_rate.py

Defines all api routes for exchange rate resources especially CRUD
"""

from flask import Blueprint

from ..resources import ExchangeRateResource

ExchangeRateBlueprint = Blueprint("exchange_rate", __name__)

ExchangeRateBlueprint.route("/exchange-rates", methods=['POST'])(ExchangeRateResource.create)
ExchangeRateBlueprint.route("/exchange-rates", methods=['GET'])(ExchangeRateResource.read_all)
ExchangeRateBlueprint.route("/exchange-rates/<uuid:id>", methods=['GET'])(ExchangeRateResource.read_one)
ExchangeRateBlueprint.route("/exchange-rates/<uuid:id>", methods=['PUT'])(ExchangeRateResource.update)
ExchangeRateBlueprint.route("/exchange-rates/<uuid:id>", methods=['DELETE'])(ExchangeRateResource.delete)
