"""
src/models/merchant.py

A shop that accepts payment through Payverve.

A merchant is a Payverve user wearing a second hat: the settlement wallet is
the owner's own NGN wallet, and the account a buyer transfers to is the owner's
BellBank virtual account. Nothing here holds money of its own.

Keys come in a pair. The public key is safe to put in a checkout page. The
secret key authenticates the shop's server and is never stored: only its keyed
hash is kept, the same treatment bvn_hash gets, so a database copy does not
hand over the ability to charge on a merchant's behalf.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel


class MerchantModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ A shop accepting payment through Payverve """

    __tablename__ = 'merchants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    business_name = db.Column(db.String(), nullable=False)

    # Safe to expose: identifies the shop to a buyer's browser.
    public_key = db.Column(db.String(), nullable=False, unique=True)

    # The secret itself is shown once at issue and never stored. This is
    # hash_identifier(secret) -- an HMAC under SECRET_KEY, so the column cannot
    # be reversed by anyone who only has the database.
    secret_key_hash = db.Column(db.String(), nullable=False, unique=True)

    # Last four characters, so a merchant can tell their own keys apart in a
    # dashboard without the key being recoverable.
    secret_key_preview = db.Column(db.String(), nullable=False)

    # Where charge events are posted. Null means the shop polls instead,
    # which is a legitimate choice, not a misconfiguration.
    webhook_url = db.Column(db.String(), nullable=True)

    # Signs outgoing webhooks so the shop can prove the request is ours.
    # Encrypted rather than hashed: unlike the secret key, we have to recover
    # the plaintext to compute the signature.
    webhook_secret = db.Column(db.String(), nullable=True)

    is_active = db.Column(db.Boolean(), nullable=False, default=True)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'),
                        nullable=False)

    # relationships

    charges = db.relationship('ChargeModel', backref='merchant', lazy=True,
                              cascade='all')
