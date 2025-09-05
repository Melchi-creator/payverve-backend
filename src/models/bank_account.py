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

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    bvn = db.Column(db.String(), unique=True, nullable=False)
    country = db.Column(db.String(), nullable=False)
    country_code = db.Column(db.String(), nullable=False)
    bank_name = db.Column(db.String(), nullable=False)
    bank_code = db.Column(db.Integer, nullable=False)
    account_name = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.BigInteger, unique=True, nullable=False)
    account_type = db.Column(db.String(), nullable=False)
    currency = db.Column(db.String(), nullable=False)
    document_type = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
