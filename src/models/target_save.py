"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class TargetSaveModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ """

    __tablename__ = 'target_saves'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    balance = db.Column(db.Text(), nullable=False)
    target_amount = db.Column(db.Integer, nullable=False)
    interval = db.Column(db.String(), nullable=False)  # hourly, daily, weekly, monthly
    title = db.Column(db.String(), nullable=False)
    is_active = db.Column(db.Boolean(), nullable=False, default=True)
    last_successful_saving = db.Column(db.DateTime(), nullable=True)
    last_attempted_saving = db.Column(db.DateTime(), nullable=False)
    next_saving = db.Column(db.DateTime(), nullable=False)
    end_date = db.Column(db.DateTime(), nullable=False)
    start_date = db.Column(db.DateTime(), nullable=False)
    is_deleted = db.Column(db.Boolean(), nullable=False, default=False)
    deleted_at = db.Column(db.DateTime(), nullable=True)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
