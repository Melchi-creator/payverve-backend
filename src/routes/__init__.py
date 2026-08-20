"""

"""

from .admin import AdminBlueprint
from .admin_role import AdminRoleBlueprint
from .authentication_authorisation import LoginBlueprint
# from .bankaccount import BankaccountBlueprint
from .beneficiary import BeneficiaryBlueprint
from .currency import CurrencyBlueprint
from .exchange_rate import ExchangeRateBlueprint
from .fixed_deposit import FixedDepositBlueprint
from .flutterwave_helper import FlutterwaveBlueprint
from .foreign_transfer import ForeignTransferBlueprint
from .kyc import KYCBlueprint
from .local_transfer import LocalTransferBlueprint
from .misc import MiscellaneousBlueprint
from .device import DeviceBlueprint
from .notification import NotificationBlueprint
from .payverve_transfer import PayverveTransferBlueprint
from .payverve_wallet import PayverveWalletBlueprint
from .referral import ReferralBlueprint
from .server import ServerBlueprint
from .spend_save import SpendSaveBlueprint
from .swap_currency import SwapCurrencyBlueprint
from .target_save import TargetSaveBlueprint
from .token_verification import TokenVerificationBlueprint
from .transation import TransactionBlueprint
from .user import UserBlueprint
from .virtual_account_numbers import VirtualAccountNumberBlueprint
from .wallet import WalletBlueprint
from .bank import BankBlueprint
# server.py registers blueprints by iterating vars(routes), so a module that is
# never imported here is never routed. bellbank_helper.py defined this
# blueprint but nothing imported it, so /bellbank/webhook did not exist on any
# deployment -- BellBank's collection notifications had nowhere to land.
from .bellbank_helper import BellbankBlueprint
