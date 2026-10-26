"""Sending money: reserve first, refund only on a certain refusal.

The old flow read the balance, called BellBank, then wrote back
(old balance - amount), wiping out any deposit credited meanwhile. After the
bank accepted it read wallet.account_number, a column wallets no longer have,
so every successful transfer answered 500 with the money gone and nothing
recorded. Spend & Save added to savings without taking it from the wallet.

Run:  ENV=development PYTHONPATH=. python tests/test_outbound_transfer.py
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

from flask import Flask, request  # noqa: E402

import src.resources  # noqa: E402,F401  (import order, see test_virtual_account)
import src.resources.local_transfer as local_transfer  # noqa: E402

from src.models import (CurrencyModel, LocalTransferModel,  # noqa: E402
                        SpendSaveModel, TransactionModel, UserModel,
                        VirtualAccountNumberModel, WalletModel, db)
from src.resources.notification import NotificationResource  # noqa: E402
from src.services import registration  # noqa: E402
from src.utilities import Cryptographer, KYCTierCheck  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []
bank = local_transfer.BellbankHelper


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


class _Response:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


def accepted(status='pending', charge=10):
    return _Response(200, {'success': True, 'data': {
        'status': status, 'charge': charge,
        'sessionId': f'SESS-{uuid.uuid4().hex[:8]}'}})


def set_balance(wallet_id, amount):
    wallet = db.session.get(WalletModel, wallet_id)
    wallet.fund = Cryptographer.encrypt(amount)
    db.session.commit()


def balance(wallet_id):
    db.session.expire_all()
    return float(Cryptographer.decrypt(
        db.session.get(WalletModel, wallet_id).fund))


def send(user_id, wallet_id, amount='1000'):
    body = {'bank_code': '010', 'amount': amount, 'narration': 'rent',
            'account_number': '1001011000', 'recipient_name': 'Test Account',
            'recipient_bank': 'Test Bank', 'user_id': str(user_id),
            'wallet_id': str(wallet_id)}

    with app.test_request_context(json=body):
        request.current_user = {'sub': str(user_id)}
        response, status = local_transfer.LocalTransferResource.create()
        return status, response.get_json()


def main():
    NotificationResource.store_and_push = staticmethod(lambda *a, **k: None)
    NotificationResource.store_nofication = staticmethod(lambda *a, **k: None)
    KYCTierCheck.kyc_transfer_check = staticmethod(lambda *a, **k: None)
    bank.bellbank_authentication = staticmethod(lambda *a, **k: 'tok')

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
        wallet.currency_ticker = 'ngn'
        db.session.add(VirtualAccountNumberModel(
            virtual_account_id='v1', account_number='9901234567',
            reference='r1', account_bank_name='bellbank',
            account_type='static', status='active', customer_code='cust_1',
            currency_ticker='NGN', is_active=True, user_id=user.id,
            currency_id=ngn.id))
        db.session.commit()
        uid, wid = user.id, wallet.id

        def transfer(reference):
            return LocalTransferModel.query.filter_by(
                reference_number=reference).one()

        # Accepted, pending at the bank: debited once, recorded, not a 500.
        set_balance(wid, 5000)
        bank.transfer_outbound = staticmethod(lambda **k: accepted())
        status, body = send(uid, wid)
        check('accepted transfer answers 201', status, 201)
        check('  wallet debited by the amount', balance(wid), 4000.0)
        row = transfer(body['data']['reference'])
        check('  recorded as pending', row.transaction_status, 'pending')
        check('  with the bank session id and charge',
              (row.session_id.startswith('SESS-'), row.charge_amount),
              (True, 10.0))
        check('  history row written', TransactionModel.query.filter_by(
            user_id=uid, transaction_title='Money Sent').count(), 1)

        # Successful straight away.
        bank.transfer_outbound = staticmethod(
            lambda **k: accepted('successful'))
        status, body = send(uid, wid, '500')
        check('successful transfer is marked successful',
              transfer(body['data']['reference']).transaction_status,
              'successful')
        check('  and debited', balance(wid), 3500.0)

        # The bank refuses: refunded, marked failed.
        bank.transfer_outbound = staticmethod(lambda **k: _Response(
            400, {'success': False, 'message': 'Invalid account'}))
        status, body = send(uid, wid)
        check('refused transfer answers 400', status, 400)
        check('  and the money is back', balance(wid), 3500.0)
        failed = LocalTransferModel.query.filter_by(
            transaction_status='failed').count()
        check('  recorded as failed', failed, 1)

        # Unknown outcome (network error, requery inconclusive): the money
        # stays reserved rather than risk paying it out twice.
        bank.transfer_outbound = staticmethod(lambda **k: None)
        bank.transfer_requery = staticmethod(lambda *a, **k: None)
        status, body = send(uid, wid)
        check('unknown outcome is accepted as processing',
              (status, body['data']['status']), (201, 'pending'))
        check('  with the money still reserved', balance(wid), 2500.0)

        # Unknown at first, but the requery says it went through.
        bank.transfer_requery = staticmethod(lambda *a, **k: _Response(
            200, {'data': {'status': 'successful', 'charge': '10.00',
                           'sessionId': 'SESS-REQ'}}))
        status, body = send(uid, wid, '100')
        check('requery settles an unknown outcome',
              transfer(body['data']['reference']).transaction_status,
              'successful')

        # Not enough money: refused before the bank is called.
        def must_not_call(**k):
            raise AssertionError('bank called for an unaffordable transfer')

        bank.transfer_outbound = staticmethod(must_not_call)
        status, body = send(uid, wid, '999999')
        check('insufficient funds refused', status, 400)
        check('  balance unchanged', balance(wid), 2400.0)

        # A deposit credited while the bank call is in flight survives.
        def deposit_during_call(**k):
            w = WalletModel.query.filter_by(id=wid).one()
            w.fund = Cryptographer.encrypt(
                float(Cryptographer.decrypt(w.fund)) + 700)
            db.session.commit()
            return accepted()

        bank.transfer_outbound = staticmethod(deposit_during_call)
        send(uid, wid, '400')
        check('a deposit during the bank call is kept', balance(wid),
              2400.0 - 400 + 700)

        # Spend & Save takes its share from the wallet, not from nowhere.
        db.session.add(SpendSaveModel(
            user_id=uid, percentage_to_save=10, is_active=True,
            balance=Cryptographer.encrypt(0)))
        db.session.commit()
        bank.transfer_outbound = staticmethod(lambda **k: accepted())
        before = balance(wid)
        send(uid, wid, '1000')
        saved = float(Cryptographer.decrypt(
            SpendSaveModel.query.filter_by(user_id=uid).one().balance))
        check('spend & save moves 10% into savings', saved, 100.0)
        check('  and takes it out of the wallet', balance(wid),
              before - 1000 - 100)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
