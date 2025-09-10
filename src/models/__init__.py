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
from .kyc import KYCModel
from .local_transfer import LocalTransferModel
from .payverve_transfer import PayverveTransferModel
from .payverve_wallet import PayverveWalletModel
from .referral import ReferralModel
from .swap_currency import SwapCurrencyModel
from .user import UserModel
from .virtual_account_numbers import VirtualAccountNumberModel
from .wallet import WalletModel
