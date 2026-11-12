"""A shop owner replaces keys and moves their webhook, safely.

A secret key or webhook secret is shown once. Before this there was no way to
replace a lost or leaked one, and no way to change where payment events go.

Also covers the webhook address itself: our server posts to it, so it must
never be a way to make Payverve call its own internal network.

Run:  ENV=development PYTHONPATH=. python tests/test_merchant_settings.py
"""
import os
import sys
import uuid
from datetime import date, datetime

from sqlalchemy import types as _satypes

_orig_bind = _satypes.Uuid.bind_processor


def _tolerant_bind(self, dialect):
    """Postgres accepts UUID strings; SQLite demands objects."""
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

from flask import Flask, request  # noqa: E402

import src.resources  # noqa: F401,E402  (load order: resources before middlewares)
import config  # noqa: E402
from src.auth.merchant_auth import merchant_required  # noqa: E402
from src.models import (CurrencyModel, MerchantModel, UserModel,  # noqa: E402
                        WalletModel, db)
from src.resources.merchant import (MerchantResource,  # noqa: E402
                                    MerchantSettingsResource)
from src.services import checkout, merchant_webhook  # noqa: E402
from src.services.registration import RegistrationError  # noqa: E402
from src.utilities import Cryptographer, decrypt_identifier  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

PIN = '123456'
_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<56} got={got!r} want={want!r}")


def make_user(tag, ngn, pin=PIN):
    user = UserModel(first_name=tag.title(), last_name='Owner',
                     email_address=f'{tag}@example.com', username=tag,
                     mobile_number=f'8060000{abs(hash(tag)) % 1000:03d}',
                     user_code=f'S{abs(hash(tag)) % 999:03d}', gender='male',
                     date_of_birth=date(1990, 1, 1), customer_code=f'c_{tag}')
    user.set_password('Abcdef1!x')
    if pin:
        user.set_transaction_pin(pin)
    db.session.add(user)
    db.session.commit()
    db.session.add(WalletModel(user_id=user.id, currency_id=ngn.id,
                               fund=Cryptographer.encrypt('0.00'),
                               currency_ticker='ngn', is_active=True))
    db.session.commit()
    return user


def as_owner(user, handler, **json):
    with app.test_request_context(method='POST', json=json):
        request.current_user = {'sub': str(user.id)}
        response, status = handler()
        return status, response.get_json()


def key_works(secret):
    """Whether the shop's server is let in with this secret key."""
    with app.test_request_context(
            headers={'Authorization': f'Bearer {secret}'}):
        result = merchant_required(lambda merchant=None: ('ok', 200))()
        return result[1] == 200


def fake_dns(answers):
    """Stand in for DNS: host -> list of addresses."""
    def getaddrinfo(host, port, *a, **k):
        if host not in answers:
            raise OSError('no such host')
        return [(2, 1, 6, '', (addr, 0)) for addr in answers[host]]
    checkout.socket.getaddrinfo = getaddrinfo


def main():
    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        owner = make_user('owner', ngn)
        stranger = make_user('stranger', ngn)

        status, body = as_owner(owner, MerchantResource.create,
                                business_name='Kebi Stores')
        old_secret = body['data']['secret_key']
        public_key = body['data']['public_key']
        old_whsec = body['data']['webhook_secret']
        check('shop registered with no webhook', status, 201)

        # --- secret key rotation ---------------------------------------
        status, body = as_owner(owner, MerchantSettingsResource.rotate_secret_key,
                                transaction_pin='000000')
        check('rotating with a wrong pin is refused', status, 400)
        check('  and the old key still works', key_works(old_secret), True)

        status, body = as_owner(owner, MerchantSettingsResource.rotate_secret_key)
        check('rotating with no pin is refused', status, 400)

        status, body = as_owner(owner, MerchantSettingsResource.rotate_secret_key,
                                transaction_pin=PIN)
        new_secret = body['data']['secret_key']
        check('rotating with the pin succeeds', status, 200)
        check('  a new secret is returned', new_secret != old_secret, True)
        check('  the old key stops working at once', key_works(old_secret),
              False)
        check('  the new key works', key_works(new_secret), True)
        check('  the public key is kept', body['data']['public_key'],
              public_key)
        merchant = MerchantModel.query.filter_by(user_id=owner.id).one()
        check('  the preview shows the new key',
              merchant.secret_key_preview, new_secret[-4:])

        status, _ = as_owner(stranger,
                             MerchantSettingsResource.rotate_secret_key,
                             transaction_pin=PIN)
        check('someone without a shop gets 404, not a key', status, 404)

        # --- webhook secret rotation -----------------------------------
        status, body = as_owner(owner,
                                MerchantSettingsResource.rotate_webhook_secret,
                                transaction_pin=PIN)
        new_whsec = body['data']['webhook_secret']
        check('webhook secret replaced', (status, new_whsec != old_whsec),
              (200, True))
        db.session.expire_all()
        merchant = MerchantModel.query.filter_by(user_id=owner.id).one()
        check('  webhooks are now signed with it',
              decrypt_identifier(merchant.webhook_secret), new_whsec)

        # --- webhook url -----------------------------------------------
        status, body = as_owner(owner, MerchantSettingsResource.update_webhook_url,
                                transaction_pin=PIN)
        check('webhook_url missing from the body is refused', status, 400)

        status, body = as_owner(owner, MerchantSettingsResource.update_webhook_url,
                                transaction_pin='000000',
                                webhook_url='https://kebi.example/hook')
        check('changing the url with a wrong pin is refused', status, 400)
        db.session.expire_all()
        check('  and nothing changed',
              MerchantModel.query.filter_by(user_id=owner.id).one().webhook_url,
              None)

        status, body = as_owner(owner, MerchantSettingsResource.update_webhook_url,
                                transaction_pin=PIN,
                                webhook_url='https://kebi.example/hook')
        check('webhook url set', (status, body['data']['webhook_url']),
              (200, 'https://kebi.example/hook'))
        check('  and reported configured', body['data']['webhook_configured'],
              True)

        status, body = as_owner(owner, MerchantSettingsResource.update_webhook_url,
                                transaction_pin=PIN, webhook_url=None)
        check('null turns webhooks off', (status, body['data']['webhook_url']),
              (200, None))

        # A shop that somehow has no signing secret is issued one with its url.
        merchant = MerchantModel.query.filter_by(user_id=owner.id).one()
        merchant.webhook_secret = None
        db.session.commit()
        status, body = as_owner(owner, MerchantSettingsResource.update_webhook_url,
                                transaction_pin=PIN,
                                webhook_url='https://kebi.example/hook')
        check('a url with no secret yet issues one',
              body['data'].get('webhook_secret', '').startswith('whsec_'),
              True)

        # --- the address must be public, outside development -----------
        was_dev = config.is_dev
        config.is_dev = False
        try:
            def refused(url):
                try:
                    checkout.clean_webhook_url(url)
                    return False
                except RegistrationError:
                    return True

            check('http is refused in production',
                  refused('http://kebi.example/hook'), True)
            for url in ('https://localhost/hook', 'https://127.0.0.1/hook',
                        'https://10.0.0.5/hook', 'https://192.168.1.1/hook',
                        'https://169.254.169.254/latest/meta-data',
                        'https://[::1]/hook', 'https://db.internal/hook',
                        'javascript:alert(1)', 'not a url'):
                check(f'  refused: {url}', refused(url), True)
            check('a public https url is accepted',
                  refused('https://kebi.example/hook'), False)

            try:
                checkout.stage_merchant(stranger, 'Bad Shop',
                                        webhook_url='https://127.0.0.1/x')
                check('registration with an internal url is refused', False,
                      True)
            except RegistrationError as e:
                check('registration with an internal url is refused',
                      e.code, 400)
            db.session.rollback()

            # A public name later repointed inside our network is caught at
            # delivery, without our server ever posting to it.
            fake_dns({'kebi.example': ['10.0.0.7'],
                      'good.example': ['93.184.216.34']})
            check('a name resolving inside our network is not public',
                  checkout.webhook_host_is_public('https://kebi.example/h'),
                  False)
            check('  an unresolvable name is not public',
                  checkout.webhook_host_is_public('https://nope.example/h'),
                  False)
            check('  a public address is',
                  checkout.webhook_host_is_public('https://good.example/h'),
                  True)

            calls = []

            class _Ok:
                status_code = 200

            def post(url, **kw):
                calls.append(kw)
                return _Ok()

            merchant_webhook.requests.post = post

            from src.models import ChargeModel
            merchant = MerchantModel.query.filter_by(user_id=owner.id).one()
            charge = checkout.stage_charge(merchant, 'ORDER-S1', '100')
            charge.status = 'paid'
            charge.paid_at = datetime.now()
            db.session.commit()

            delivery = merchant_webhook.enqueue_charge_paid(charge, merchant)
            db.session.commit()
            result = merchant_webhook.attempt(delivery.id)
            check('delivery to a repointed host is not sent', len(calls), 0)
            check('  it is a failed attempt that will retry',
                  (result.status, result.attempts,
                   result.next_attempt_at is not None), ('pending', 1, True))

            fake_dns({'kebi.example': ['93.184.216.34']})
            result = merchant_webhook.attempt(delivery.id)
            check('once public again it is delivered', result.status,
                  'delivered')
            check('  without following redirects',
                  calls[-1].get('allow_redirects'), False)
        finally:
            config.is_dev = was_dev

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
