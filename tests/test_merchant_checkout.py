"""A shop takes payment through Payverve.

Covers the whole path: registering a merchant, a shop server raising a charge
with its secret key, the buyer's checkout view (amount, who to pay, the
BellBank account to transfer to, and the countdown), and settling from a
Payverve balance.

Run:  ENV=development PYTHONPATH=. python tests/test_merchant_checkout.py
"""
import os
import sys
import uuid
from datetime import date, datetime, timedelta

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

from flask import Flask  # noqa: E402

import src.resources  # noqa: F401,E402  (load order: resources before middlewares)
from src.models import (ChargeModel, CurrencyModel,  # noqa: E402
                        VirtualAccountNumberModel, WalletModel, UserModel, db)
from src.resources.charge import ChargeResource, CheckoutResource  # noqa: E402
from src.resources.merchant import MerchantResource  # noqa: E402
from src.services import checkout  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
# The charge routes build the checkout page URL with url_for.
from src.routes.charge import ChargeBlueprint  # noqa: E402
app.register_blueprint(ChargeBlueprint)

PIN = '123456'
_failures = []
_seq = iter(range(1, 99))


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


def make_user(tag, ngn, balance, with_account=None):
    n = next(_seq)
    user = UserModel(first_name=tag.title(), last_name='Test',
                     email_address=f'{tag}@example.com', username=tag,
                     mobile_number=f'80200000{n:02d}', user_code=f'U{n:03d}',
                     gender='male', date_of_birth=date(1990, 1, 1),
                     customer_code=f'cust_{tag}')
    user.set_password('Abcdef1!x')
    user.set_transaction_pin(PIN)
    db.session.add(user)
    db.session.commit()

    db.session.add(WalletModel(user_id=user.id, currency_id=ngn.id,
                               fund=Cryptographer.encrypt(str(balance)),
                               currency_ticker='ngn', is_active=True))
    db.session.commit()

    if with_account:
        db.session.add(VirtualAccountNumberModel(
            virtual_account_id=f'va-{n}', account_number=with_account,
            reference=f'ref-{n}', account_bank_name='bellbank microfinance bank',
            account_type='static', status='active', customer_code=f'cust_{tag}',
            currency_ticker='NGN', is_active=True, user_id=user.id,
            currency_id=ngn.id))
        db.session.commit()
    return user


def as_user(user_id, **json):
    ctx = app.test_request_context(json=json)
    ctx.push()
    from flask import request
    request.current_user = {'sub': str(user_id)}
    return ctx


def body_of(response):
    payload, status = response
    return payload.get_json(), status


def main():
    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        owner = make_user('shopowner', ngn, 0.00, with_account='1000999111')
        buyer = make_user('buyer', ngn, 5000.00)

        # --- the shop registers ----------------------------------------
        ctx = as_user(owner.id, business_name='Kebi Stores')
        data, status = body_of(MerchantResource.create())
        ctx.pop()
        check('merchant registered', status, 201)
        secret = data['data']['secret_key']
        check('  a public key is issued',
              data['data']['public_key'].startswith('pk_'), True)
        check('  the secret is returned exactly once',
              secret.startswith('sk_'), True)

        ctx = as_user(owner.id)
        data, status = body_of(MerchantResource.read_mine())
        ctx.pop()
        check('profile never returns the secret again',
              'secret_key' in data['data'], False)
        check('  it shows the settlement account',
              data['data']['settlement_account_number'], '1000999111')

        # --- the shop server raises a charge ---------------------------
        def post_charge(ref, amount, key=secret):
            with app.test_request_context(
                    json={'reference': ref, 'amount': amount,
                          'callback_url': 'https://shop.example/thanks'},
                    headers={'Authorization': f'Bearer {key}'}):
                from src.auth.merchant_auth import merchant_required
                return body_of(merchant_required(ChargeResource.create)())

        data, status = post_charge('ORDER-1', '1500.00')
        check('charge created with the secret key', status, 201)
        code = data['data']['charge_code']
        check('  amount is echoed', data['data']['amount'], '1500.00')
        check('  a countdown is returned',
              data['data']['seconds_remaining'] > 0, True)

        again, _ = post_charge('ORDER-1', '1500.00')
        check('same reference returns the same charge, not a second one',
              again['data']['charge_code'], code)

        bad, status = post_charge('ORDER-2', '100.00', key='sk_live_wrong')
        check('a wrong secret key is refused', status, 401)

        # --- the buyer opens the checkout ------------------------------
        with app.test_request_context():
            data, status = body_of(CheckoutResource.read(charge_code=code))
        check('checkout opens without a session', status, 200)
        view = data['data']
        check('  shows the shop', view['business_name'], 'Kebi Stores')
        check('  shows the amount', view['amount'], '1500.00')
        check('  offers bank transfer', view['bank_transfer']['available'], True)
        check('  to the merchant BellBank account',
              view['bank_transfer']['account_number'], '1000999111')
        check('  and counts down', view['seconds_remaining'] > 0, True)
        check('  return url carries the shop reference',
              view['return_url'],
              f'https://shop.example/thanks?reference=ORDER-1&charge_code={code}')

        # --- the checkout page a shop sends its buyer to ---------------
        check('checkout_url is the absolute page url',
              again['data']['checkout_url'],
              f'http://localhost/pay/{code}')

        def page(c):
            with app.test_request_context():
                r = CheckoutResource.page(charge_code=c)
                return r.status_code, r.get_data(as_text=True), r.headers

        status, html, headers = page(code)
        check('checkout page opens without a session', status, 200)
        check('  shows the shop and amount',
              ('Kebi Stores' in html, '1,500.00' in html), (True, True))
        check('  shows the account to transfer to', '1000999111' in html, True)
        check('  polls the json route',
              f'data-status-url="/checkout/{code}"' in html, True)
        check('  is never cached', headers['Cache-Control'], 'no-store')
        check('  has no inline script (CSP blocks it)',
              '<script>' in html, False)
        check('an unknown code is a 404 page', page('nope')[0], 404)

        with app.test_request_context(
                json={'reference': 'ORDER-JS', 'amount': '10',
                      'callback_url': 'javascript:alert(1)'},
                headers={'Authorization': f'Bearer {secret}'}):
            from src.auth.merchant_auth import merchant_required
            _, status = body_of(merchant_required(ChargeResource.create)())
        check('a non-http callback_url is refused', status, 400)

        # --- the buyer pays from their Payverve balance ----------------
        ctx = as_user(buyer.id, transaction_pin='000000')
        data, status = body_of(CheckoutResource.pay_with_wallet(charge_code=code))
        ctx.pop()
        check('a wrong pin is refused', status, 400)

        ctx = as_user(buyer.id, transaction_pin=PIN)
        data, status = body_of(CheckoutResource.pay_with_wallet(charge_code=code))
        ctx.pop()
        check('payment from wallet succeeds', status, 200)

        def balance(user):
            w = WalletModel.query.filter_by(user_id=user.id).first()
            return float(Cryptographer.decrypt(w.fund))

        check('  buyer debited', balance(buyer), 3500.00)
        check('  shop credited', balance(owner), 1500.00)
        check('  charge marked paid',
              ChargeModel.query.filter_by(charge_code=code).first().status,
              'paid')

        ctx = as_user(buyer.id, transaction_pin=PIN)
        data, status = body_of(CheckoutResource.pay_with_wallet(charge_code=code))
        ctx.pop()
        check('paying twice is refused', status, 409)
        check('  and nothing moved again', balance(buyer), 3500.00)

        # --- the shop verifies, which is the only answer it should trust
        with app.test_request_context(
                headers={'Authorization': f'Bearer {secret}'}):
            from src.auth.merchant_auth import merchant_required
            data, status = body_of(
                merchant_required(ChargeResource.verify)(reference='ORDER-1'))
        check('shop verifies the charge as paid', data['data']['paid'], True)

        # --- the window closes ------------------------------------------
        data, _ = post_charge('ORDER-3', '250.00')
        stale = ChargeModel.query.filter_by(
            charge_code=data['data']['charge_code']).first()
        stale.expires_at = datetime.now() - timedelta(seconds=1)
        db.session.commit()

        ctx = as_user(buyer.id, transaction_pin=PIN)
        data, status = body_of(
            CheckoutResource.pay_with_wallet(charge_code=stale.charge_code))
        ctx.pop()
        check('an expired charge cannot be paid', status, 410)
        check('  buyer untouched', balance(buyer), 3500.00)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
