"""
src/models/payverve_transfer.py
This module defines the PayverveTransferModel class, which represents a transfer made through Payverve.
It includes fields for the transfer amount, narration, account details, reference, transaction type,
and transfer pair, along with timestamps for creation and updates. It also establishes foreign key relationships
with the users and wallets tables.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class PayverveTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Payverve Transfer Model """

    __tablename__ = 'payverve_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount_from_sender = db.Column(db.Text, nullable=False)
    amount_to_recipient = db.Column(db.Text, nullable=False)
    coversion_rate = db.Column(db.String(), nullable=False)
    narration = db.Column(db.String(), nullable=True)
    wallet_identifier = db.Column(db.BigInteger, nullable=False)
    reference = db.Column(db.String(), nullable=False, unique=True)
    transaction_type = db.Column(db.String(), nullable=False, default="wallet_tranfer")
    transfer_pair = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
