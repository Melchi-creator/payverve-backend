"""

"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class NotificationModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ """

    __tablename__ = 'notifications'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = db.Column(db.String(), nullable=False)
    body = db.Column(db.Text(), nullable=False)
    topic = db.Column(db.String(), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(), db.ForeignKey('users.id'), nullable=True)
    admin_id = db.Column(UUID(), db.ForeignKey('admins.id'), nullable=True)
