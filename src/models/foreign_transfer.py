"""
foreign_transfer.py

Defines the model structure for foreign transfer
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class ForeignTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Foreign Transfer Model """

    __tablename__ = 'foreign_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount = db.Column(db.Float(), nullable=False)
    narration = db.Column(db.String(), nullable=True)
    account = db.Column(db.Integer, nullable=False)
    swift_code = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(), nullable=False)
    bank = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # foreign keys

    user = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
