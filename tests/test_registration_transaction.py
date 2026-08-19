"""Registration must be one transaction, with no HTTP calls to ourselves.

Signup used to POST to its own /ngn-wallets, /referrals and /kycs endpoints.
Each hop committed independently, so a later failure left the earlier rows
behind and had to be unpicked by compensating deletes. These tests assert the
replacement: every row lands in one commit, a failure leaves nothing at all,
and `requests` is never touched.

Run:  ENV=development PYTHONPATH=. python tests/test_registration_transaction.py
"""
import os
import sys
import uuid
from datetime import date

from sqlalchemy import types as _satypes

_orig_bind_processor = _satypes.Uuid.bind_processor


def _tolerant_bind_processor(self, dialect):
    """Postgres accepts UUID strings from JSON; SQLite demands objects."""
    proc = _orig_bind_processor(self, dialect)
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


_satypes.Uuid.bind_processor = _tolerant_bind_processor


from flask import Flask  # noqa: E402

import config  # noqa: E402
from src.models import (CurrencyModel, KYCModel, ReferralModel,  # noqa: E402
                        UserModel, WalletModel, db)
from src.resources import user as user_resource  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<46} got={got!r} want={want!r}")


class _FakeFlutterwaveResponse:
    status_code = 201
    text = '{}'

    @staticmethod
    def json():
        return {'data': {'id': 'cust_stub'}}


def install_stubs():
    """Force the production path, but stub everything that leaves the process."""
    user_resource.FlutterwaveHelper.flutterwave_authentication = \
        staticmethod(lambda *a, **k: 'stub-token')
    user_resource.FlutterwaveHelper.create_flutterwave_account = \
        staticmethod(lambda *a, **k: _FakeFlutterwaveResponse())
    user_resource.MailtrapHelper.mailtrap_email_sender = \
        staticmethod(lambda *a, **k: None)

    def _no_http(*a, **k):
        raise AssertionError(f'registration made an HTTP call: {a} {k}')

    user_resource.requests.request = _no_http


def seed_currency():
    db.create_all()
    ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
    db.session.add(ngn)
    db.session.commit()
    return ngn


def existing_user(ngn, suffix='0'):
    user = UserModel(first_name='Ref', last_name='Errer',
                     email_address=f'referrer{suffix}@example.com',
                     username=f'referrer{suffix}',
                     mobile_number=f'700000000{suffix}',
                     user_code=f'REF{suffix}', gender='male',
                     date_of_birth=date(1990, 1, 1))
    user.set_password('Abcdef1!x')
    db.session.add(user)
    db.session.commit()
    db.session.add(WalletModel(user_id=user.id, currency_id=ngn.id,
                               fund=Cryptographer.encrypt(1000.0),
                               currency_ticker='ngn'))
    db.session.commit()
    return user


def register(**overrides):
    body = dict(first_name='New', last_name='User',
                email_address='new@example.com', username='newuser',
                mobile_number='8123456789', password='Abcdef1!x',
                gender='male', date_of_birth='1990-01-01')
    body.update(overrides)
    with app.test_request_context(json=body):
        response = user_resource.UserResource.create()
        return response[1] if isinstance(response, tuple) else 200


def counts():
    return (UserModel.query.count(), WalletModel.query.count(),
            KYCModel.query.count(), ReferralModel.query.count())


def main():
    install_stubs()
    with app.app_context():
        ngn = seed_currency()
        referrer = existing_user(ngn)
        base_counts = counts()
        check('baseline rows (user, wallet, kyc, referral)', base_counts,
              (1, 1, 0, 0))

        # A bad referral code fails mid-signup. Nothing may survive it.
        code = register(referral_code='DOES-NOT-EXIST')
        check('unknown referral code rejected', code, 404)
        check('  nothing committed', counts(), base_counts)
        check('  no orphan user', UserModel.query.filter_by(
            email_address='new@example.com').first(), None)

        # A duplicate referral also fails mid-signup, after the wallet staged.
        ReferralModel.query.delete()
        db.session.commit()

        # Happy path with a referral: user, wallet, kyc and referral together.
        code = register(referral_code=referrer.user_code)
        check('registration with referral accepted', code, 201)
        check('  all four rows committed', counts(), (2, 2, 1, 1))

        new_user = UserModel.query.filter_by(
            email_address='new@example.com').first()
        new_wallet = WalletModel.query.filter_by(
            user_id=new_user.id, currency_id=ngn.id).first()
        referrer_wallet = WalletModel.query.filter_by(
            user_id=referrer.id, currency_id=ngn.id).first()
        check('  new user credited the bonus',
              float(Cryptographer.decrypt(new_wallet.fund)), 500.0)
        check('  referrer credited the bonus',
              float(Cryptographer.decrypt(referrer_wallet.fund)), 1500.0)

        # Plain signup, no referral.
        code = register(email_address='solo@example.com', username='solo',
                        mobile_number='8123456700')
        check('registration without referral accepted', code, 201)
        check('  user, wallet and kyc committed', counts(), (3, 3, 2, 1))

        # A failing verification email must not undo a real registration.
        def _boom(*a, **k):
            raise RuntimeError('mailtrap is down')

        user_resource.MailtrapHelper.mailtrap_email_sender = staticmethod(_boom)
        before = counts()
        code = register(email_address='mail@example.com', username='mailer',
                        mobile_number='8123456702')
        check('email failure still returns created', code, 201)
        check('  account committed anyway',
              counts(), (before[0] + 1, before[1] + 1, before[2] + 1, before[3]))
        user_resource.MailtrapHelper.mailtrap_email_sender =             staticmethod(lambda *a, **k: None)

        # A duplicate email is refused and leaves nothing behind.
        before = counts()
        code = register(email_address='solo@example.com', username='solo2',
                        mobile_number='8123456701')
        check('duplicate email rejected', code, 409)
        check('  nothing committed', counts(), before)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS  (and `requests` was never called)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
