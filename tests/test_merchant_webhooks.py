"""A shop is told when a charge is paid, and told again if it did not hear.

Delivery is signed, so a shop can prove the request came from Payverve and was
not forged by someone who guessed the endpoint. That is the lesson from the
other side of this: BellBank sends us webhooks with no signature at all.

Run:  ENV=development PYTHONPATH=. python tests/test_merchant_webhooks.py
"""
import hashlib
import hmac
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import types as _satypes

_orig_bind = _satypes.Uuid.bind_processor


def _tolerant_bind(self, dialect):
    proc = _orig_bind(self, dialect)
    if proc is None:
        return None

    def go(value):
        if isinstance(value, str):
            try:
                value = uuid.UUID(value)
            except ValueError:
                pass
        return proc(value)

    return go


_satypes.Uuid.bind_processor = _tolerant_bind

from flask import Flask  # noqa: E402

import src.resources  # noqa: F401,E402  (load order: resources before middlewares)
from src.models import (ChargeModel, CurrencyModel, UserModel,  # noqa: E402
                        WalletModel, WebhookDeliveryModel, db)
from src.services import checkout, merchant_webhook  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

HOOK = 'https://shop.example/payverve-webhook'
_failures = []
_sent = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


class _Response:
    def __init__(self, status_code):
        self.status_code = status_code


def responder(status=200, explode=False):
    """Stands in for the shop's server."""
    def post(url, data=None, headers=None, timeout=None, **kw):
        _sent.append({'url': url, 'body': data, 'headers': headers or {}})
        if explode:
            raise ConnectionError('shop server unreachable')
        return _Response(status)
    return post


def make_shop(ngn, tag, webhook_url=HOOK):
    user = UserModel(first_name=tag.title(), last_name='Owner',
                     email_address=f'{tag}@example.com', username=tag,
                     mobile_number=f'8050000{abs(hash(tag)) % 1000:03d}',
                     user_code=f'W{abs(hash(tag)) % 999:03d}', gender='male',
                     date_of_birth=date(1990, 1, 1), customer_code=f'c_{tag}')
    user.set_password('Abcdef1!x')
    db.session.add(user)
    db.session.commit()
    db.session.add(WalletModel(user_id=user.id, currency_id=ngn.id,
                               fund=Cryptographer.encrypt('0.00'),
                               currency_ticker='ngn', is_active=True))
    merchant, _sk, whsec = checkout.stage_merchant(
        user, f'{tag.title()} Stores', webhook_url=webhook_url)
    db.session.commit()
    return merchant, whsec


def main():
    import src.services.merchant_webhook as mw

    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        merchant, webhook_secret = make_shop(ngn, 'signed')
        charge = checkout.stage_charge(merchant, 'ORDER-W1', '1500.00')
        charge.status = 'paid'
        charge.method = 'wallet'
        charge.paid_at = datetime.now()
        charge.settlement_reference = 'PVC-ABC'
        db.session.commit()

        delivery = merchant_webhook.enqueue_charge_paid(charge, merchant)
        db.session.commit()
        check('a paid charge queues a delivery', delivery is not None, True)
        check('  addressed to the shop', delivery.target_url, HOOK)
        check('  not yet sent', delivery.status, 'pending')

        mw.requests.post = responder(200)
        result = merchant_webhook.attempt(delivery.id)
        check('delivery to a healthy shop succeeds', result.status, 'delivered')
        check('  one attempt', result.attempts, 1)
        check('  nothing left to retry', result.next_attempt_at, None)

        sent = _sent[-1]
        body = sent['body']
        check('  the event header is set',
              sent['headers'].get('X-Payverve-Event'), 'charge.paid')

        # The shop verifies exactly as our docs tell it to.
        expected = hmac.new(webhook_secret.encode(), body,
                            hashlib.sha256).hexdigest()
        check('  the signature verifies with the shop secret',
              hmac.compare_digest(sent['headers'].get('X-Payverve-Signature', ''),
                                  expected), True)
        check('  a wrong secret does not verify',
              hmac.compare_digest(
                  sent['headers'].get('X-Payverve-Signature', ''),
                  hmac.new(b'whsec_wrong', body, hashlib.sha256).hexdigest()),
              False)
        check('  tampering with the body breaks the signature',
              hmac.compare_digest(
                  sent['headers'].get('X-Payverve-Signature', ''),
                  hmac.new(webhook_secret.encode(),
                           body.replace(b'1500.00', b'1.00'),
                           hashlib.sha256).hexdigest()),
              False)

        payload = json.loads(body)
        check('  carries the shop reference',
              payload['data']['reference'], 'ORDER-W1')
        check('  and the amount', payload['data']['amount'], '1500.00')

        # A shop that is down is retried, not dropped.
        merchant2, _ = make_shop(ngn, 'down')
        charge2 = checkout.stage_charge(merchant2, 'ORDER-W2', '800.00')
        charge2.status = 'paid'
        charge2.paid_at = datetime.now()
        db.session.commit()
        d2 = merchant_webhook.enqueue_charge_paid(charge2, merchant2)
        db.session.commit()

        mw.requests.post = responder(explode=True)
        r2 = merchant_webhook.attempt(d2.id)
        check('an unreachable shop leaves the delivery pending',
              r2.status, 'pending')
        check('  and schedules a retry', r2.next_attempt_at is not None, True)
        check('  recording why', 'ConnectionError' in (r2.last_error or ''), True)

        mw.requests.post = responder(500)
        r2 = merchant_webhook.attempt(d2.id)
        check('a 500 from the shop also retries', r2.status, 'pending')
        check('  recording the status', r2.last_status_code, 500)

        # It gives up eventually rather than retrying for ever.
        r2.attempts = merchant_webhook.MAX_ATTEMPTS - 1
        r2.next_attempt_at = datetime.now() - timedelta(seconds=1)
        db.session.commit()
        r2 = merchant_webhook.attempt(r2.id)
        check('it gives up after the last attempt', r2.status, 'failed')
        check('  with nothing further scheduled', r2.next_attempt_at, None)

        # The scheduled job picks up what is due and nothing else.
        merchant3, _ = make_shop(ngn, 'later')
        charge3 = checkout.stage_charge(merchant3, 'ORDER-W3', '300.00')
        charge3.status = 'paid'
        charge3.paid_at = datetime.now()
        db.session.commit()
        d3 = merchant_webhook.enqueue_charge_paid(charge3, merchant3)
        d3.next_attempt_at = datetime.now() + timedelta(minutes=30)
        db.session.commit()
        check('a delivery not yet due is left alone',
              [d.id for d in merchant_webhook.due_deliveries()], [])

        d3.next_attempt_at = datetime.now() - timedelta(seconds=1)
        db.session.commit()
        mw.requests.post = responder(200)
        tally = merchant_webhook.retry_due()
        check('the retry run delivers what is due', tally['delivered'], 1)
        check('  and nothing is left pending',
              WebhookDeliveryModel.query.filter_by(status='pending').count(), 0)

        # A shop with no webhook configured is not an error.
        merchant4, _ = make_shop(ngn, 'poller', webhook_url=None)
        charge4 = checkout.stage_charge(merchant4, 'ORDER-W4', '100.00')
        db.session.commit()
        check('a shop without a webhook queues nothing',
              merchant_webhook.enqueue_charge_paid(charge4, merchant4), None)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
