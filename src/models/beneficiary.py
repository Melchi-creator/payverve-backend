"""
beneficiary.py

Defines the model structure for users beneficiaries
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class BeneficiaryModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Beneficiary Model """

    __tablename__ = 'beneficiaries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.Integer, nullable=False)
    bank = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=False)

    # foreign keys

    user = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
