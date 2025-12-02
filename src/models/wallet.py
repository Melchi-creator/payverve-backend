"""
src/models/wallet.py
This module defines the WalletModel class, which represents a user's wallet in the database.
It includes fields for the fund, wallet identifier, timestamps for creation and updates,
and establishes foreign key relationships with the users and currencies tables.
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
    account_number = db.Column(db.BigInteger(), nullable=False, unique=True, default='00000000000')
    account_type = db.Column(db.String(), nullable=False, default='individual')
    external_reference = db.Column(db.String(), nullable=False, unique=True)
    validity_type = db.Column(db.String(), nullable=False, default='permanent')
    bank_name = db.Column(db.String(), nullable=False, default='payverve bank')
    currency_ticker = db.Column(db.String(), nullable=False, default='ngn')
    is_active = db.Column(db.Boolean(), default=False, nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)

    # relationships

    foreign_transfers = db.relationship('ForeignTransferModel', backref='wallets', lazy=True, cascade="all")
    local_transfers = db.relationship('LocalTransferModel', backref='wallets', lazy=True, cascade="all")
    payverve_transfers = db.relationship('PayverveTransferModel', backref='wallets', lazy=True, cascade="all")
