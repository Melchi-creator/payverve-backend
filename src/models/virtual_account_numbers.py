"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class VirtualAccountNumberModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """  """

    __tablename__ = 'virtual_account_numbers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    account_number = db.Column(db.BigInteger(), nullable=False, unique=True)
    reference = db.Column(db.String(), nullable=False, unique=True)
    account_bank_name = db.Column(db.String(), nullable=False)
    account_type = db.Column(db.String(), nullable=False, default='static')
    status = db.Column(db.String(), nullable=False, default='active')
    account_expiration_datetime = db.Column(db.DateTime(), nullable=False)
    customer_code = db.Column(db.String(), nullable=False)
    currency_ticker = db.Column(db.String(), nullable=False, default='NGN')
    is_active = db.Column(db.Boolean(), default=True, nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
