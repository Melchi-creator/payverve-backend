"""
models

Hold all models import
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .admin import AdminModel
from .admin_roles import AdminRoleModel
from .bank_account import BankAccountModel
from .beneficiary import BeneficiaryModel
from .currency import CurrencyModel
from .exchange_rate import ExchangeRateModel
from .foreign_transfer import ForeignTransferModel
from .local_transfer import LocalTransferModel
from .payverve_transfer import PayverveTransferModel
from .swap_currency import SwapCurrencyModel
from .user import UserModel
from .wallet import WalletModel
