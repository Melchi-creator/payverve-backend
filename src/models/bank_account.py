"""
bank_account.py

Defines the model structure for bank accounts
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class BankAccountModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Bank Account Model """

    __tablename__ = 'bank_accounts'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    bank_name = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.BigInteger, nullable=False)
    bank_swift = db.Column(db.String(), nullable=False)
    account_first_name = db.Column(db.String(), nullable=False)
    account_last_name = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # foreign keys

    user = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
