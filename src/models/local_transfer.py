"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class LocalTransferModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ Local Transfer Model """

    __tablename__ = 'local_transfers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    amount_from_sender = db.Column(db.Text, nullable=False)
    amount_to_recipient = db.Column(db.Text, nullable=False)
    sender_name = db.Column(db.String(), nullable=False)
    sender_bank = db.Column(db.String(), nullable=False)
    narration = db.Column(db.String(), nullable=True)
    wallet_identifier = db.Column(db.BigInteger, nullable=False)
    recipient_name = db.Column(db.String(), nullable=False)
    recipient_bank = db.Column(db.String(), nullable=False)
    account_number = db.Column(db.BigInteger, nullable=False)
    reference_number = db.Column(db.String(), nullable=False)
    transfer_type = db.Column(db.String(), nullable=False, default="local_tranfer")

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    wallet_id = db.Column(UUID(as_uuid=True), db.ForeignKey('wallets.id'), nullable=False)
