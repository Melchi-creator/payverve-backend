"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class SpendSaveModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ """

    __tablename__ = 'spend_saves'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    balance = db.Column(db.Text(), nullable=False)
    percentage_to_save = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
