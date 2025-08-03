"""
wallet.py

Defines the model structure for wallets
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class WalletModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Wallet Model """

    __tablename__ = 'wallets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fund = db.Column(db.Text, nullable=False)
    wallet_identifier = db.Column(db.BigInteger, nullable=False, unique=True)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)

    # relationships

    foreign_transfers = db.relationship('ForeignTransferModel', backref='wallets', lazy=True, cascade="all")
    local_transfers = db.relationship('LocalTransferModel', backref='wallets', lazy=True, cascade="all")
    payverve_transfers = db.relationship('PayverveTransferModel', backref='wallets', lazy=True, cascade="all")
