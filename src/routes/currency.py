"""
currency.py

Defines all api routes for users resources especially CRUD
"""

from flask import Blueprint

from ..resources import CurrencyResource

CurrencyBlueprint = Blueprint("currency", __name__)

CurrencyBlueprint.route("/currencies", methods=['POST'])(CurrencyResource.create)
CurrencyBlueprint.route("/currencies", methods=['GET'])(CurrencyResource.read_all)
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['GET'])(CurrencyResource.read_one)
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['PUT'])(CurrencyResource.update)
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['DELETE'])(CurrencyResource.delete)
