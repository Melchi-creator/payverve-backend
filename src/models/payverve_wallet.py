"""
src/models/payverve_wallet.py
this module defines the PayverveWalletModel class, which represents a wallet in the Payverve system.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class PayverveWalletModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Payverve Wallet Model """

    __tablename__ = 'payverve_wallets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fund = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)
