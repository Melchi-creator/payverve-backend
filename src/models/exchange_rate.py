"""
exchange_rate.py

Defines the model structure for exchange rates
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class ExchangeRateModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Exchange Rate Model """

    __tablename__ = 'exchange_rates'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    base_currency = db.Column(db.String(), nullable=False)
    target_currency = db.Column(db.String(), nullable=False)
    rate = db.Column(db.Float(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)
