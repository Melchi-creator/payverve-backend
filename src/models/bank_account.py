"""
bank_account.py

Defines the model structure for bank accounts
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


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

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
