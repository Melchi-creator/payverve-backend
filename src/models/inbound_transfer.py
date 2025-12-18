"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class InboundTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """  """

    __tablename__ = 'inbound_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = db.Column(db.Text, nullable=False)
    charge_amount = db.Column(db.Float, nullable=False, default=0.0)
    sender_name = db.Column(db.String(), nullable=False)
    sender_bank = db.Column(db.String(), nullable=False)
    sender_account_number = db.Column(db.BigInteger, nullable=False)
    narration = db.Column(db.String(), nullable=True)
    recipient_name = db.Column(db.String(), nullable=False)
    recipient_bank = db.Column(db.String(), nullable=False, default="Payverve Bank")
    recipient_account_number = db.Column(db.BigInteger, nullable=False)
    reference_number = db.Column(db.String(), nullable=False)
    session_id = db.Column(db.String(), nullable=False, unique=True)
    stamp_duty = db.Column(db.Float, nullable=False, default=0.0)
    transfer_type = db.Column(db.String(), nullable=False, default="payverve-inbound_transfer")
    transfer_pair = db.Column(db.String(), nullable=False, default='ngn-ngn')
    transaction_status = db.Column(db.String(), nullable=False)  # pending, successful, failed

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
