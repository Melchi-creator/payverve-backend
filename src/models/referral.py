"""

"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class ReferralModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ """

    __tablename__ = 'referrals'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    referral_id = db.Column(db.String(), nullable=False)
    referral_code = db.Column(db.String(), nullable=False)
    referred_id = db.Column(db.String(), nullable=False)
    referred_code = db.Column(db.String(), nullable=False)

    created_at = db.Column(db.DateTime(), default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now(), nullable=True)
