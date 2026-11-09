"""A bank transfer from a buyer settles the shop's charge.

The buyer is shown the merchant's BellBank account and pays from any bank app.
Nothing in that transfer says which order it is for, so the charge is matched
on the amount the buyer SENT -- before BellBank's fee, since that is the figure
the shop quoted.

The match is staged in the same transaction as the credit: a deposit must never
be credited while the charge it paid is left pending.

Run:  ENV=development PYTHONPATH=. python tests/test_charge_matching.py
"""
import os
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

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
from src.models import (ChargeModel, CurrencyModel, MerchantModel,  # noqa: E402
                        UserModel, VirtualAccountNumberModel, WalletModel, db)
from src.services import checkout  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []
_seq = iter(range(1, 99))


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<54} got={got!r} want={want!r}")


def make_merchant(ngn, tag='shop'):
    n = next(_seq)
    user = UserModel(first_name=tag.title(), last_name='Owner',
                     email_address=f'{tag}@example.com', username=tag,
                     mobile_number=f'80300000{n:02d}', user_code=f'M{n:03d}',
                     gender='male', date_of_birth=date(1990, 1, 1),
                     customer_code=f'cust_{tag}')
    user.set_password('Abcdef1!x')
    db.session.add(user)
    db.session.commit()

    wallet = WalletModel(user_id=user.id, currency_id=ngn.id,
                         fund=Cryptographer.encrypt('0.00'),
                         currency_ticker='ngn', is_active=True)
    db.session.add(wallet)
    db.session.add(VirtualAccountNumberModel(
        virtual_account_id=f'va-{n}', account_number=f'10009{n:05d}',
        reference=f'ref-{n}', account_bank_name='bellbank microfinance bank',
        account_type='static', status='active', customer_code=f'cust_{tag}',
        currency_ticker='NGN', is_active=True, user_id=user.id,
        currency_id=ngn.id))
    merchant, _secret = checkout.stage_merchant(user, f'{tag.title()} Stores')
    db.session.commit()
    return user, wallet, merchant


def raise_charge(merchant, reference, amount):
    charge = checkout.stage_charge(merchant, reference, amount)
    db.session.commit()
    return charge


def main():
    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        owner, wallet, merchant = make_merchant(ngn)
        charge = raise_charge(merchant, 'ORDER-A', '2500.00')

        # A buyer sends exactly the quoted amount. BellBank takes a fee on the
        # way in, so the wallet is credited less -- matching must use the sent
        # figure, not the credited one.
        matched = checkout.match_inbound_payment(wallet, 2500.00, 'SESSION-1')
        db.session.commit()
        check('a transfer of the quoted amount settles the charge',
              matched is not None and matched.reference, 'ORDER-A')
        check('  marked paid', ChargeModel.query.filter_by(
            reference='ORDER-A').first().status, 'paid')
        check('  recorded as a transfer', ChargeModel.query.filter_by(
            reference='ORDER-A').first().method, 'transfer')
        check('  traceable to the bank session', ChargeModel.query.filter_by(
            reference='ORDER-A').first().settlement_reference, 'SESSION-1')

        # One transfer settles one charge. A replayed notification must not
        # settle a second: the shop would ship two orders for one payment.
        # The webhook rejects a repeated sessionId upstream, but this must
        # hold on its own.
        raise_charge(merchant, 'ORDER-A2', '2500.00')
        again = checkout.match_inbound_payment(wallet, 2500.00, 'SESSION-1')
        db.session.commit()
        check('a replayed session settles nothing further', again, None)
        check('  the next charge is still open', ChargeModel.query.filter_by(
            reference='ORDER-A2').first().status, 'pending')
        check('  the paid charge keeps its session',
              ChargeModel.query.filter_by(
                  reference='ORDER-A').first().settlement_reference, 'SESSION-1')

        # An amount nobody is owed is just a deposit.
        stray = checkout.match_inbound_payment(wallet, 77.00, 'SESSION-2')
        db.session.commit()
        check('a transfer matching no charge settles nothing', stray, None)

        # A closed window must not be settled.
        stale = raise_charge(merchant, 'ORDER-B', '900.00')
        stale.expires_at = datetime.now() - timedelta(seconds=1)
        db.session.commit()
        missed = checkout.match_inbound_payment(wallet, 900.00, 'SESSION-3')
        db.session.commit()
        check('an expired charge is not settled by a late transfer',
              missed, None)
        check('  and stays unpaid', ChargeModel.query.filter_by(
            reference='ORDER-B').first().status, 'pending')

        # Two open charges for the same amount: oldest first, both settle as
        # each payment arrives.
        first = raise_charge(merchant, 'ORDER-C1', '400.00')
        later = raise_charge(merchant, 'ORDER-C2', '400.00')
        later.created_at = first.created_at + timedelta(seconds=5)
        db.session.commit()

        one = checkout.match_inbound_payment(wallet, 400.00, 'SESSION-4')
        db.session.commit()
        check('with two identical charges the oldest settles first',
              one.reference, 'ORDER-C1')
        two = checkout.match_inbound_payment(wallet, 400.00, 'SESSION-5')
        db.session.commit()
        check('  the second payment settles the other', two.reference,
              'ORDER-C2')

        # A wallet with no merchant behind it is an ordinary customer.
        n = next(_seq)
        plain = UserModel(first_name='Plain', last_name='Customer',
                          email_address='plain@example.com', username='plain',
                          mobile_number=f'80400000{n:02d}', user_code=f'P{n:03d}',
                          gender='male', date_of_birth=date(1990, 1, 1),
                          customer_code='cust_plain')
        plain.set_password('Abcdef1!x')
        db.session.add(plain)
        db.session.commit()
        plain_wallet = WalletModel(user_id=plain.id, currency_id=ngn.id,
                                   fund=Cryptographer.encrypt('0.00'),
                                   currency_ticker='ngn', is_active=True)
        db.session.add(plain_wallet)
        db.session.commit()
        check('a deposit to a non-merchant settles nothing',
              checkout.match_inbound_payment(plain_wallet, 2500.00, 'SESSION-6'),
              None)

        # Another shop's charge must never be settled by this shop's deposit.
        _o2, wallet2, merchant2 = make_merchant(ngn, tag='rival')
        mine = raise_charge(merchant2, 'RIVAL-1', '5000.00')
        crossed = checkout.match_inbound_payment(wallet, 5000.00, 'SESSION-7')
        db.session.commit()
        check('one shop cannot settle another shop charge', crossed, None)
        check('  the other shop charge is still pending',
              ChargeModel.query.filter_by(reference='RIVAL-1').first().status,
              'pending')

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
