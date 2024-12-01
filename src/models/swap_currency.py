"""
swap_currency.py

Defines the model structure for swapping currencies
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class SwapCurrencyModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Swap Currency Model """

    __tablename__ = 'swap_currencies'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    base_currency = db.Column(db.String(), nullable=False)
    target_currency = db.Column(db.String(), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    transaction_type = db.Column(db.String(), nullable=False, default="swap")
    currency_pair = db.Column(db.String(), nullable=False)
    amount_received = db.Column(db.Float(), nullable=False)
    reference = db.Column(db.String(), nullable=False, unique=True)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # foreign keys

    user = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
