"""
swap_currency.py

Defines the model structure for swapping currencies
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class SwapCurrencyModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Swap Currency Model """

    __tablename__ = 'swap_currencies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount_from_base_currency = db.Column(db.Text, nullable=False)
    amount_to_target_currency = db.Column(db.Text, nullable=False)
    coversion_rate = db.Column(db.String(), nullable=False)
    narration = db.Column(db.String(), nullable=True)
    wallet_identifier = db.Column(db.BigInteger, nullable=False)  # target wallet
    reference = db.Column(db.String(), nullable=False, unique=True)
    transaction_type = db.Column(db.String(), nullable=False, default="currencies_swap")
    swap_pairs = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)  # base wallet
