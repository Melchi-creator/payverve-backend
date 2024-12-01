"""
wallet.py

Defines the model structure for wallets
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class WalletModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Wallet Model """

    __tablename__ = 'wallets'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    fund = db.Column(db.Float(), nullable=False, default=0)
    account_number = db.Column(db.BigInteger, nullable=False, unique=True)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # foreign keys

    user = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)

    # relationships

    foreign_transfers = db.relationship('ForeignTransferModel', backref='wallets', lazy=True, cascade="all")
    local_transfers = db.relationship('LocalTransferModel', backref='wallets', lazy=True, cascade="all")
    payverve_transfers = db.relationship('PayverveTransferModel', backref='wallets', lazy=True, cascade="all")
