"""Regression tests for the referral bonus.

POST /referrals credits two wallets 500 each. It had no jwt_required and was
gated only by a `created_by_payverve` boolean taken from the request body, so
any unauthenticated caller could mint bonuses on repeat. It also committed the
referral row before the credits, in three separate transactions, so a failure
part-way through left a referral on record that paid nobody.

Run:  ENV=development PYTHONPATH=. python tests/test_referral_bonus.py
"""
import sys
import uuid
from datetime import date

# The resource passes UUIDs straight from JSON as strings. Postgres accepts
# that; SQLite's Uuid bind processor demands a uuid.UUID. Shim it so these tests
# exercise the real code path rather than a dialect quirk.
from sqlalchemy import types as _satypes

_orig_bind_processor = _satypes.Uuid.bind_processor


def _tolerant_bind_processor(self, dialect):
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
from src.models import (CurrencyModel, ReferralModel, UserModel,  # noqa: E402
                        WalletModel, db)
from src.resources.referral import ReferralResource  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

START = 1000.0
BONUS = 500.0

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

SECRET_HEADER = getattr(config, 'internal_api_secret_header',
                        'X-Payverve-Internal')
AUTH = {SECRET_HEADER: config.internal_api_secret}

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<44} got={got!r} want={want!r}")


def seed():
    db.create_all()
    ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
    db.session.add(ngn)
    db.session.commit()

    users = []
    for i, name in enumerate(('referrer', 'referred')):
        user = UserModel(first_name=name, last_name='Test',
                         email_address=f'{name}@example.com', username=name,
                         mobile_number=f'80000000{i}', user_code=f'CODE{i}',
                         gender='male', date_of_birth=date(1990, 1, 1))
        user.set_password('Abcdef1!x')
        db.session.add(user)
        db.session.commit()

        db.session.add(WalletModel(user_id=user.id, currency_id=ngn.id,
                                   fund=Cryptographer.encrypt(START),
                                   currency_ticker='ngn'))
        db.session.commit()
        users.append(user)
    return ngn, users


def balance(user_id, currency_id):
    wallet = WalletModel.query.filter_by(
        user_id=user_id, currency_id=currency_id).first()
    return float(Cryptographer.decrypt(wallet.fund)) if wallet else None


def post(payload, headers=AUTH):
    with app.test_request_context(json=payload, headers=headers):
        response = ReferralResource.create()
        return response[1] if isinstance(response, tuple) else 200


def main():
    with app.app_context():
        ngn, (referrer, referred) = seed()
        body = dict(referral_id=str(referrer.id),
                    referral_code=referrer.user_code,
                    referred_id=str(referred.id),
                    referred_code=referred.user_code,
                    email_address=referred.email_address,
                    created_by_payverve=True)

        check('unknown user rejected',
              post({**body, 'email_address': 'nobody@example.com'}), 404)
        check('  referrer balance untouched', balance(referrer.id, ngn.id), START)
        check('  no referral row written', ReferralModel.query.count(), 0)

        check('created_by_payverve=False rejected',
              post({**body, 'created_by_payverve': False}), 403)
        check('  referrer balance untouched', balance(referrer.id, ngn.id), START)

        check('self-referral rejected',
              post({**body, 'referral_id': str(referred.id)}), 400)
        check('  balance untouched', balance(referred.id, ngn.id), START)

        check('missing ngn wallet rejected',
              post({**body, 'referral_id': str(uuid.uuid4())}), 404)
        check('  no orphan referral row', ReferralModel.query.count(), 0)

        check('missing internal secret rejected', post(body, headers={}), 403)
        check('  referrer balance untouched', balance(referrer.id, ngn.id), START)

        check('wrong internal secret rejected',
              post(body, headers={SECRET_HEADER: 'wrong'}), 403)
        check('  referrer balance untouched', balance(referrer.id, ngn.id), START)

        check('valid referral accepted', post(body), 201)
        check('  referrer credited', balance(referrer.id, ngn.id), START + BONUS)
        check('  referred credited', balance(referred.id, ngn.id), START + BONUS)
        check('  exactly one referral row', ReferralModel.query.count(), 1)

        check('replay rejected', post(body), 409)
        check('  referrer not paid twice',
              balance(referrer.id, ngn.id), START + BONUS)
        check('  referred not paid twice',
              balance(referred.id, ngn.id), START + BONUS)
        check('  still one referral row', ReferralModel.query.count(), 1)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
