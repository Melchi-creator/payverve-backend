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
    response_code = db.Column(db.String(), nullable=False)
    response_message = db.Column(db.String(), nullable=False)
    flw_ref = db.Column(db.String(), nullable=False)
    order_ref = db.Column(db.String(), nullable=False)
    frequency = db.Column(db.String(), nullable=False)
    created_at_by_flw = db.Column(db.DateTime(), nullable=False)
    expiry_date = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.String(), nullable=False, unique=True)
    bank_name = db.Column(db.String(), nullable=False)
    note = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency_ticker = db.Column(db.String(), nullable=False)
    is_active = db.Column(db.Boolean(), default=True, nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
