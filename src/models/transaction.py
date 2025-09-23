"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class TransactionModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """  """

    __tablename__ = 'transactions'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tx_ref = db.Column(db.String(), nullable=True)
    flw_ref = db.Column(db.String(), nullable=True)
    amount = db.Column(db.Text, nullable=False)
    transaction_type = db.Column(db.String(), nullable=False)
    note = db.Column(db.String(), nullable=True)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    currency_id = db.Column(UUID(as_uuid=True), db.ForeignKey('currencies.id'), nullable=False)
