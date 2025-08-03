"""
local_transfer.py

Defines the model structure for local transfer
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class LocalTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Local Transfer Model """

    __tablename__ = 'local_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = db.Column(db.Text, nullable=False)
    narration = db.Column(db.String(), nullable=True)
    account = db.Column(db.BigInteger, nullable=False)
    name = db.Column(db.String(), nullable=False)
    bank = db.Column(db.String(), nullable=False)
    rference_number = db.Column(db.String(), nullable=False)
    transfer_type = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
