"""
payverve_transfer.py

Defines the model structure for payverve transfer
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
    amount = db.Column(db.Float(), nullable=False)
    narration = db.Column(db.String(), nullable=True)
    account = db.Column(db.BigInteger, nullable=False)
    reference = db.Column(db.String(), nullable=False, unique=True)
    transaction_type = db.Column(db.String(), nullable=False, default="wallet tranfer")
    transfer_pair = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
