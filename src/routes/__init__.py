"""
routes
Hold all routed import
"""

from .admin_roles import AdminRoleBlueprint
# from .bankaccount import BankaccountBlueprint
from .beneficiary import BeneficiaryBlueprint
from .currency import CurrencyBlueprint
from .server import ServerBlueprint
from .user import UserBlueprint
from .wallet import WalletBlueprint
