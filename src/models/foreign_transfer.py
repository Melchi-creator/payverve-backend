"""
foreign_transfer.py

Defines the model structure for foreign transfer
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class ForeignTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Foreign Transfer Model """

    __tablename__ = 'foreign_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(), nullable=False)
    sender_bank = db.Column(db.String(), nullable=False, default="Payverve Bank")
    narration = db.Column(db.String(), nullable=True)
    recipient_name = db.Column(db.String(), nullable=False)
    recipient_bank = db.Column(db.String(), nullable=False)
    recipient_account_number = db.Column(db.BigInteger, nullable=False)
    swift_code = db.Column(db.Integer, nullable=False)
    reference_number = db.Column(db.String(), nullable=False)
    transfer_type = db.Column(db.String(), nullable=False, default="payverve-international_banks_transfer")
    transfer_pair = db.Column(db.String(), nullable=False)
    transaction_status = db.Column(db.String(), nullable=False)  # pending, successful, failed

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
