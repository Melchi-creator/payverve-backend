"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class KYCModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ """

    __tablename__ = 'kycs'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tier = db.Column(db.Integer, nullable=False, default=1)
    bvn = db.Column(db.String(), nullable=True, unique=True)
    nin = db.Column(db.String(), nullable=True, unique=True)
    bvn_present = db.Column(db.Boolean(), nullable=False, default=False)
    nin_present = db.Column(db.Boolean(), nullable=False, default=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
