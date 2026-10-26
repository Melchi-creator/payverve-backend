"""A BellBank deposit must be credited once, completely, or not at all.

Both crediting paths saved the new balance first and then read
wallet.user -- a relationship that does not exist (it is wallet.users). Every
deposit raised after the balance was committed: no inbound record, no history,
no fee taken, and the webhook still answered 200. The inbound record is what
marks a sessionId as processed, so every retry credited the wallet again.

Run:  ENV=development PYTHONPATH=. python tests/test_inbound_credit.py
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

import src.resources  # noqa: E402,F401  (import order, see test_virtual_account)
import src.middlewares as middlewares  # noqa: E402

from src.models import (CurrencyModel, InboundTransferModel,  # noqa: E402
                        TransactionModel, UserModel,
                        VirtualAccountNumberModel, WalletModel, db)
from src.resources.notification import NotificationResource  # noqa: E402
from src.services import registration  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

ACCOUNT = '9901234567'
_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


def notification(session_id, amount='500.00', fee=20, account=ACCOUNT):
    return {
        'event': 'collection', 'virtualAccount': account,
        'amountReceived': amount, 'transactionFee': fee, 'stampDuty': 0,
        'sessionId': session_id, 'sourceAccountName': 'Ada Obi',
        'sourceAccountNumber': '0123456789', 'sourceBankName': 'Test Bank',
        'remarks': 'rent', 'externalReference': f'ext-{session_id}',
        'status': 'successful',
    }


def balance(wallet_id):
    db.session.expire_all()
    return float(Cryptographer.decrypt(db.session.get(WalletModel, wallet_id).fund))


def main():
    # Pushes and stored notifications are side effects; keep them quiet.
    NotificationResource.store_and_push = staticmethod(lambda *a, **k: None)
    NotificationResource.store_nofication = staticmethod(lambda *a, **k: None)
    helper = middlewares.BellbankHelper

    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        user = UserModel(first_name='Ada', last_name='Obi',
                         email_address='ada@example.com', username='ada',
                         mobile_number='8012345678', user_code='ADA1',
                         gender='female', date_of_birth=date(1990, 1, 1),
                         customer_code='cust_1')
        user.set_password('Abcdef1!x')
        db.session.add(user)
        db.session.commit()

        wallet = registration.stage_ngn_wallet(user.id, ngn.id)
        db.session.add(VirtualAccountNumberModel(
            virtual_account_id='v1', account_number=ACCOUNT, reference='r1',
            account_bank_name='bellbank', account_type='static',
            status='active', customer_code='cust_1', currency_ticker='NGN',
            is_active=True, user_id=user.id, currency_id=ngn.id))
        db.session.commit()
        wallet_id = wallet.id
        start = balance(wallet_id)

        # One deposit: credited net of the fee, with its records.
        body, status = helper.others_to_payverve_transfer(
            notification('S-1'), wallet)
        check('deposit is credited', status, 201)
        check('  balance rises by amount less fee', balance(wallet_id),
              start + 480.0)
        check('  inbound record written',
              InboundTransferModel.query.filter_by(session_id='S-1').count(), 1)
        flows = sorted((t.transaction_flow, Cryptographer.decrypt(t.amount))
                       for t in TransactionModel.query.filter_by(
                           user_id=user.id).all())
        check('  history has the credit and the fee', flows,
              [('credit', '500.00'), ('debit', '20.00')])

        # The same notification again (BellBank retries): no second credit.
        body, status = helper.others_to_payverve_transfer(
            notification('S-1'), db.session.get(WalletModel, wallet_id))
        check('a repeated sessionId is acknowledged', status, 200)
        check('  and not credited again', balance(wallet_id), start + 480.0)

        # Payverve-to-Payverve goes through the same code.
        body, status = helper.payverve_to_payverve_transfer(
            notification('S-2', amount='100.00', fee=0),
            db.session.get(WalletModel, wallet_id))
        check('internal transfer is credited', status, 201)
        check('  with no fee row when the fee is 0', balance(wallet_id),
              start + 580.0)

        # A failure part way writes nothing, and reports 5xx so BellBank
        # retries.
        original = TransactionModel.__init__

        def explode(self, *a, **k):
            raise RuntimeError('database went away')

        TransactionModel.__init__ = explode
        body, status = helper.others_to_payverve_transfer(
            notification('S-3'), db.session.get(WalletModel, wallet_id))
        TransactionModel.__init__ = original
        check('a failed credit reports 5xx', status, 500)
        check('  and leaves the balance untouched', balance(wallet_id),
              start + 580.0)
        check('  and records no inbound row, so a retry can credit it',
              InboundTransferModel.query.filter_by(session_id='S-3').count(), 0)

        body, status = helper.others_to_payverve_transfer(
            notification('S-3'), db.session.get(WalletModel, wallet_id))
        check('  the retry then succeeds', (status, balance(wallet_id)),
              (201, start + 1060.0))

        # Bad notifications are refused without touching the wallet.
        body, status = helper.others_to_payverve_transfer(
            notification('S-4', account='0000000000'),
            db.session.get(WalletModel, wallet_id))
        check('a notification for another account is refused', status, 400)
        no_session = notification('x')
        no_session['sessionId'] = None
        body, status = helper.others_to_payverve_transfer(
            no_session, db.session.get(WalletModel, wallet_id))
        check('a notification without a sessionId is refused', status, 400)
        body, status = helper.others_to_payverve_transfer(
            notification('S-5', amount='0'),
            db.session.get(WalletModel, wallet_id))
        check('a zero amount is refused', status, 400)
        check('  none of those moved money', balance(wallet_id),
              start + 1060.0)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
