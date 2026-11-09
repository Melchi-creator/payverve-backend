"""
src/models/webhook_delivery.py

One attempt to tell a shop that something happened.

Every delivery is a row, not a fire-and-forget call. A shop's server will be
down, slow, or behind a proxy that drops the request, and a payment it never
hears about is an order never shipped. The row is what makes a retry possible
and what lets a shop ask later what we tried to send.

The payload is frozen at enqueue time. Re-serialising it at delivery would let
a later edit change what a shop is told about an event that already happened.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import UUID

from . import db
from .abc import BaseModel, MetaBaseModel

PENDING = 'pending'
DELIVERED = 'delivered'
FAILED = 'failed'

# Backoff between attempts, in seconds. Six tries over roughly an hour: long
# enough to ride out a restart or a short outage, short enough that a shop is
# not told about an order the next morning.
RETRY_SCHEDULE = [30, 120, 600, 1800, 3600]
MAX_ATTEMPTS = len(RETRY_SCHEDULE) + 1


class WebhookDeliveryModel(db.Model, BaseModel, metaclass=MetaBaseModel):
    """ One attempt to notify a merchant """

    __tablename__ = 'webhook_deliveries'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    event = db.Column(db.String(), nullable=False)

    # Where it is being sent, copied from the merchant at enqueue time so a
    # later change of webhook_url cannot redirect an event already queued.
    target_url = db.Column(db.String(), nullable=False)

    # The exact bytes signed and sent, frozen at enqueue.
    payload = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(), nullable=False, default=PENDING)
    attempts = db.Column(db.Integer(), nullable=False, default=0)

    last_status_code = db.Column(db.Integer(), nullable=True)
    last_error = db.Column(db.String(), nullable=True)

    next_attempt_at = db.Column(db.DateTime(), nullable=True)
    delivered_at = db.Column(db.DateTime(), nullable=True)

    created_at = db.Column(db.DateTime(), default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime(), onupdate=datetime.now, nullable=True)

    # foreign keys

    merchant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('merchants.id'),
                            nullable=False)
    charge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('charges.id'),
                          nullable=True)
