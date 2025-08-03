"""
src/routes/currency.py
This module defines the routes for managing currencies.
It includes routes for creating, reading, updating, and deleting currencies,
utilizing the CurrencyResource class.
"""

from flask import Blueprint

from ..middlewares import jwt_required
from ..resources import CurrencyResource

CurrencyBlueprint = Blueprint("currency", __name__)

CurrencyBlueprint.route("/currencies", methods=['POST'])(jwt_required(CurrencyResource.create))
CurrencyBlueprint.route("/currencies", methods=['GET'])(jwt_required(CurrencyResource.read_all))
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['GET'])(jwt_required(CurrencyResource.read_one))
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['PUT'])(jwt_required(CurrencyResource.update))
CurrencyBlueprint.route("/currencies/<uuid:id>", methods=['DELETE'])(jwt_required(CurrencyResource.delete))
