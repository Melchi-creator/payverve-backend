"""
exchange_rate.py

Defines the model structure for exchange rates
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class ExchnageRateModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Exchange Rate Model """

    __tablename__ = 'exchange_rates'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    base_currency = db.Column(db.String(), nullable=False)
    target_currency = db.Column(db.String(), nullable=False)
    rate = db.Column(db.Integer, nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)
