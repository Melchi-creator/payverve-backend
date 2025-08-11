"""
src/models/currency.py
This module defines the CurrencyModel class, which represents a currency in the application.
It includes fields for currency information, relationships with other models, and metadata for database operations.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class CurrencyModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Currency Model """

    __tablename__ = 'currencies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(), nullable=False)
    short_code = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # relationships

    wallets = db.relationship('WalletModel', backref='currencies', lazy=True, cascade="all")
    bank_accounts = db.relationship('BankAccountModel', backref='currencies', lazy=True)
