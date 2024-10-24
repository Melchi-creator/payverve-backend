"""
currency.py

Defines the model structure for currencies
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class CurrencyModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Currency Model """

    __tablename__ = 'currencies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(), nullable=False)
    short_code = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # relationships

    wallets = db.relationship('WalletModel', backref='currencies', lazy=True, cascade="all")
    bank_accounts = db.relationship('BankAccountModel', backref='currencies', lazy=True)
