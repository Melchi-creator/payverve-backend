"""
src/middlewares/__init__.py
This module initializes the middlewares package.
"""

from .authentication import Authentication
from .authorisation import jwt_required
from .exchange_rate_api import ExchangeRate
