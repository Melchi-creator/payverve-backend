"""
admin_roles.py

Defines the model structure for admin roles
"""
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class AdminRoleModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Admin Role Model """

    __tablename__ = 'admin_roles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    role = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=False)

    # relationships

    admins = db.relationship('AdminModel', backref='admin_roles', lazy=True)
