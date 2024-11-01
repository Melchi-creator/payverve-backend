"""
routes
Hold all routed import
"""

from .currency import CurrencyBlueprint
from .exchange_rate import ExchangeRateBlueprint
from .local_transfer import LocalTransferBlueprint
from .payverve_transfer import PayverveTransferBlueprint
from .server import ServerBlueprint
from .swap_currency import SwapCurrencyBlueprint
from .user import UserBlueprint
from .wallet import WalletBlueprint
