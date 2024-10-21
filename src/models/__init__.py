"""
models

Hold all models import
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .admin import AdminModel
from .admin_roles import AdminRoleModel
from .bank_account import BankAccountModel
from .currency import CurrencyModel
from .exchange_rate import ExchnageRateModel
from .user import UserModel
from .wallet import WalletModel
