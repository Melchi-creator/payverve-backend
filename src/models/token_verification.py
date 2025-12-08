"""
src/models/token_verification.py
This module defines the TokenVerificationModel class, which represents
the token verification model in the database.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class TokenVerificationModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ this class represents the token verification model in the database."""

    __tablename__ = "token_verifications"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
    channel = db.Column(db.String(), nullable=False)
    channel_contact = db.Column(db.String(), nullable=False)
    code_sent = db.Column(db.Text, nullable=False)
    expiration_time = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime(), nullable=False)
    status = db.Column(db.String(), nullable=False)  # pending, verified, expired

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)
