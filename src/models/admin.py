"""
admin.py

Defines the model structure for admins
"""
from uuid import uuid4

from sqlalchemy import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from . import db
from .abc import BaseModel, MetaBaseModel
from ..middlewares import NetworkDateTime


class AdminModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Admin Model """

    __tablename__ = 'admins'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    first_name = db.Column(db.String(), nullable=False)
    last_name = db.Column(db.String(), nullable=False)
    middle_name = db.Column(db.String(), nullable=True)
    email_address = db.Column(db.String(), nullable=False, unique=True)
    mobile_number = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)
    gender = db.Column(db.String(), nullable=False)
    date_of_birth = db.Column(db.Date(), nullable=False)
    house_number = db.Column(db.String(), nullable=True)
    street_name = db.Column(db.String(), nullable=True)
    city = db.Column(db.String(), nullable=True)
    state = db.Column(db.String(), nullable=True)
    zipcode = db.Column(db.Integer, nullable=True)
    country = db.Column(db.String(), nullable=True)
    photo = db.Column(db.String(), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime(), default=NetworkDateTime.network_datetime(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=NetworkDateTime.network_datetime(), nullable=True)

    # foreign keys

    admin_role = db.Column(UUID(as_uuid=True), db.ForeignKey('admin_roles.id'), nullable=False)

    def set_password(self, password):
        """ hashes user password """

        self.password = generate_password_hash(password)

    def check_password(self, password):
        """ verify hashed user password """

        return check_password_hash(self.password, password)
