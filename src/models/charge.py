"""
src/models/charge.py

One intended payment to a merchant.

A charge is created by the shop's server before the buyer is sent to Payverve,
and is the only thing either side should trust afterwards. The shop asks
Payverve whether its own `reference` is paid; it must never conclude that from
the buyer being redirected back, which the buyer controls.

`amount` is a plain Numeric, not an encrypted string like WalletModel.fund.
A wallet balance is a secret; the price of a basket is not, and it has to be
compared and summed.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID, UniqueConstraint

from . import db
from .abc import BaseModel, MetaBaseModel

# A charge is a held intent, not a standing invoice: the buyer is shown an
# account number and a countdown, and an unpaid charge stops being payable so
# a stale page cannot be settled hours later against a changed basket.
CHARGE_TTL_SECONDS = 30 * 60

PENDING = 'pending'
PAID = 'paid'
EXPIRED = 'expired'

PAID_BY_WALLET = 'wallet'
PAID_BY_TRANSFER = 'transfer'


class ChargeModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ One intended payment to a merchant """

    __tablename__ = 'charges'
    __table_args__ = (
        # A shop retrying "create charge for order 1234" must get the same
        # charge back, not a second one the buyer could also pay.
        UniqueConstraint('merchant_id', 'reference',
                         name='uq_charges_merchant_reference'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # The shop's own identifier for this payment -- its order number, usually.
    reference = db.Column(db.String(), nullable=False)

    # Ours, and the only part that appears in a URL a buyer can see. Not
    # guessable, because knowing one lets you watch a stranger's checkout.
    charge_code = db.Column(db.String(), nullable=False, unique=True)

    amount = db.Column(db.Numeric(18, 2), nullable=False)
    currency_ticker = db.Column(db.String(), nullable=False, default='ngn')

    status = db.Column(db.String(), nullable=False, default=PENDING)

    # 'wallet' or 'transfer'; null until the buyer picks one and pays.
    method = db.Column(db.String(), nullable=True)

    # Where the buyer is returned to. Informational only: the shop confirms by
    # asking Payverve, never by trusting this redirect.
    callback_url = db.Column(db.String(), nullable=True)

    expires_at = db.Column(db.DateTime(), nullable=False)
    paid_at = db.Column(db.DateTime(), nullable=True)

    # Ties a paid charge back to the money that settled it: a
    # PayverveTransferModel reference for the wallet path, or the BellBank
    # session id for the transfer path.
    settlement_reference = db.Column(db.String(), nullable=True)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    merchant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('merchants.id'),
                            nullable=False)

    def is_expired(self):
        """Whether the window to pay this charge has closed."""
        return self.status == PENDING and datetime.now() >= self.expires_at

    def seconds_remaining(self):
        """Seconds left to pay, never negative. Drives the checkout countdown."""
        return max(0, int((self.expires_at - datetime.now()).total_seconds()))
