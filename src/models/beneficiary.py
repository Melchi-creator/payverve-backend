"""
beneficiary.py

Defines the model structure for users beneficiaries
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class BeneficiaryModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Beneficiary Model """

    __tablename__ = 'beneficiaries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.BigInteger, nullable=False)
    bank = db.Column(db.String(), nullable=False)
    country = db.Column(db.String(), nullable=False)
    where = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
