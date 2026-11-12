"""Telling a shop that a charge was paid.

A shop should not have to poll. When a charge settles, Payverve posts the event
to the shop's `webhook_url`, signed so the shop can prove the request came from
us and was not forged by someone who guessed the endpoint.

The signature is the lesson from the other side of this: BellBank sends us
webhooks with no signature at all, which left an IP allowlist as the only way
to tell a real notification from a forged one. We are not going to hand our
merchants that problem.

Delivery never happens inside the request that caused it. A shop's server being
slow must not hold a buyer's payment response open -- the same mistake that had
signup waiting up to 60s on a mail provider.
"""
import hashlib
import hmac
import json
from datetime import datetime, timedelta

import requests

from ..models import MerchantModel, WebhookDeliveryModel, db
from ..models.webhook_delivery import (DELIVERED, FAILED, MAX_ATTEMPTS,
                                       PENDING, RETRY_SCHEDULE)
from ..utilities import decrypt_identifier

# (connect, read). A shop's endpoint is someone else's server: it may accept
# the connection and never answer.
WEBHOOK_TIMEOUT = (5, 15)

SIGNATURE_HEADER = 'X-Payverve-Signature'
EVENT_HEADER = 'X-Payverve-Event'
CHARGE_PAID = 'charge.paid'


def sign(secret, raw_payload):
    """HMAC-SHA256 of the exact bytes sent, hex encoded.

    A shop verifies by computing the same over the raw request body. It must
    compare with a constant-time function, and must sign the body as received
    rather than a re-serialised copy -- key order and whitespace change the
    digest.
    """
    return hmac.new(secret.encode(), raw_payload, hashlib.sha256).hexdigest()


def _merchant_secret(merchant):
    """The merchant's webhook signing secret, or None if never issued."""
    if not merchant.webhook_secret:
        return None

    return decrypt_identifier(merchant.webhook_secret)


def enqueue_charge_paid(charge, merchant):
    """Queue a `charge.paid` notification. Does not commit, does not send.

    Returns the delivery row, or None when the shop has no webhook configured
    -- which is normal: a shop may choose to poll instead.
    """
    if not merchant or not merchant.webhook_url:
        return None

    payload = json.dumps({
        'event': CHARGE_PAID,
        'data': {
            'reference': charge.reference,
            'charge_code': charge.charge_code,
            'amount': f'{charge.amount:.2f}',
            'currency': charge.currency_ticker.upper(),
            'status': charge.status,
            'method': charge.method,
            'paid_at': charge.paid_at.isoformat() if charge.paid_at else None,
            'settlement_reference': charge.settlement_reference,
        },
    }, separators=(',', ':'), sort_keys=True)

    # noinspection PyArgumentList
    delivery = WebhookDeliveryModel(
        event=CHARGE_PAID,
        target_url=merchant.webhook_url,
        payload=payload,
        status=PENDING,
        attempts=0,
        next_attempt_at=datetime.now(),
        merchant_id=merchant.id,
        charge_id=charge.id,
    )
    db.session.add(delivery)
    return delivery


def attempt(delivery_id):
    """Send one delivery and record what happened. Commits its own row.

    Takes an id rather than an instance because this runs on a background
    thread, after the request that queued it has ended and taken its session
    with it.
    """
    delivery = WebhookDeliveryModel.query.filter_by(id=delivery_id).first()

    if not delivery or delivery.status == DELIVERED:
        return None

    merchant = MerchantModel.query.filter_by(id=delivery.merchant_id).first()
    secret = _merchant_secret(merchant) if merchant else None

    if not secret:
        delivery.status = FAILED
        delivery.last_error = 'no webhook secret on the merchant'
        db.session.add(delivery)
        db.session.commit()
        return delivery

    raw = delivery.payload.encode()
    delivery.attempts += 1

    from .checkout import webhook_host_is_public

    try:
        # Re-checked at every send: a name that was public when the shop
        # saved it can later be repointed at our internal network. A refusal
        # is a failed attempt, backing off like any unreachable shop.
        if not webhook_host_is_public(delivery.target_url):
            raise ValueError('webhook host does not resolve to a public '
                             'address')

        response = requests.post(
            delivery.target_url,
            data=raw,
            headers={
                'Content-Type': 'application/json',
                EVENT_HEADER: delivery.event,
                SIGNATURE_HEADER: sign(secret, raw),
            },
            timeout=WEBHOOK_TIMEOUT,
            # A redirect would send our signed request to an address that
            # was never checked. A 3xx is simply a failed attempt.
            allow_redirects=False,
        )
        delivery.last_status_code = response.status_code

        # Any 2xx is taken as accepted. A shop that answers 200 and then drops
        # the event on the floor is beyond our reach, which is why the verify
        # endpoint stays the authority.
        if 200 <= response.status_code < 300:
            delivery.status = DELIVERED
            delivery.delivered_at = datetime.now()
            delivery.next_attempt_at = None
            delivery.last_error = None
        else:
            delivery.last_error = f'HTTP {response.status_code}'
    except Exception as error:
        delivery.last_status_code = None
        delivery.last_error = f'{type(error).__name__}: {error}'[:300]

    if delivery.status != DELIVERED:
        if delivery.attempts >= MAX_ATTEMPTS:
            delivery.status = FAILED
            delivery.next_attempt_at = None
            print(f'[webhook] giving up on {delivery.event} for merchant '
                  f'{delivery.merchant_id} after {delivery.attempts} attempts: '
                  f'{delivery.last_error}. The shop can still verify the '
                  f'charge.')
        else:
            wait = RETRY_SCHEDULE[delivery.attempts - 1]
            delivery.next_attempt_at = datetime.now() + timedelta(seconds=wait)

    db.session.add(delivery)
    db.session.commit()
    return delivery


def due_deliveries(limit=50):
    """Queued deliveries whose next attempt is due."""
    return WebhookDeliveryModel.query.filter(
        WebhookDeliveryModel.status == PENDING,
        WebhookDeliveryModel.next_attempt_at <= datetime.now(),
    ).order_by(WebhookDeliveryModel.next_attempt_at.asc()).limit(limit).all()


def retry_due(limit=50):
    """Send every delivery that is due. Returns a tally for the caller."""
    tally = {'attempted': 0, 'delivered': 0, 'failed': 0, 'still_pending': 0}

    for delivery in due_deliveries(limit):
        result = attempt(delivery.id)
        tally['attempted'] += 1

        if result is None:
            continue
        if result.status == DELIVERED:
            tally['delivered'] += 1
        elif result.status == FAILED:
            tally['failed'] += 1
        else:
            tally['still_pending'] += 1

    return tally
