"""Pending transfers are settled from BellBank's answer, and refunded once.

Most BellBank transfers are 'pending' when accepted and nothing looked at them
again: completed ones stayed pending, failed or reversed ones never gave the
money back.

Run:  ENV=development PYTHONPATH=. python tests/test_transfer_settlement.py
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
import src.middlewares as middlewares  # noqa: E402
from src.resources.local_transfer import LocalTransferResource  # noqa: E402

from src.models import (CurrencyModel, LocalTransferModel,  # noqa: E402
                        TransactionModel, UserModel, WalletModel, db)
from src.resources.notification import NotificationResource  # noqa: E402
from src.services import registration, transfer_status  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []
bank = middlewares.BellbankHelper


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


def bank_says(status, reversed_flag=None, charge='20.00'):
    bank.transfer_requery = staticmethod(lambda *a, **k: _Response(200, {
        'data': {'status': status, 'charge': charge,
                 'reversedFlag': reversed_flag}}))


def balance(wallet_id):
    db.session.expire_all()
    return float(Cryptographer.decrypt(
        db.session.get(WalletModel, wallet_id).fund))


def pending_transfer(user, wallet, amount=100.0):
    """A transfer as the send flow leaves it: wallet already debited."""
    w = db.session.get(WalletModel, wallet.id)
    w.fund = Cryptographer.encrypt(
        float(Cryptographer.decrypt(w.fund)) - amount)
    reference = uuid.uuid4().hex[:24]
    transfer = LocalTransferModel(
        amount=Cryptographer.encrypt(f'{amount:.2f}'), charge_amount=0.0,
        sender_name='Ada Obi', sender_account_number=9901234567,
        narration='rent', recipient_name='Test Account',
        recipient_bank='Test Bank', recipient_account_number=1001011000,
        reference_number=reference, session_id=reference, stamp_duty=0.0,
        sender_bank='bellbank', user_id=user.id, wallet_id=wallet.id,
        transaction_status='pending')
    db.session.add(transfer)
    db.session.add(TransactionModel(
        tx_ref=reference, amount=Cryptographer.encrypt(f'{amount:.2f}'),
        transaction_type='domestic_transfer', user_id=user.id,
        currency_id=wallet.currency_id, status='pending',
        name='Test Account', transaction_flow='debit',
        transaction_title='Money Sent', currency_ticker='ngn'))
    db.session.commit()
    return transfer.id, reference


def statuses(transfer_id, reference):
    db.session.expire_all()
    history = TransactionModel.query.filter_by(tx_ref=reference).one()
    return (db.session.get(LocalTransferModel, transfer_id).transaction_status,
            history.status)


def main():
    NotificationResource.store_and_push = staticmethod(lambda *a, **k: None)
    NotificationResource.store_nofication = staticmethod(lambda *a, **k: None)
    bank.bellbank_authentication = staticmethod(lambda *a, **k: 'tok')

    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        def make_user(n):
            u = UserModel(first_name='Ada', last_name='Obi',
                          email_address=f'ada{n}@example.com',
                          username=f'ada{n}', mobile_number=f'801234567{n}',
                          user_code=f'ADA{n}', gender='female',
                          date_of_birth=date(1990, 1, 1),
                          customer_code=f'cust_{n}')
            u.set_password('Abcdef1!x')
            db.session.add(u)
            db.session.commit()
            w = registration.stage_ngn_wallet(u.id, ngn.id)
            w.fund = Cryptographer.encrypt(1000)
            db.session.commit()
            return u, w

        user, wallet = make_user(1)
        other, _ = make_user(2)
        wid = wallet.id

        # Successful: marked so, both rows, no money moves.
        tid, ref = pending_transfer(user, wallet)
        bank_says('successful')
        result = transfer_status.settle_transfer(tid)
        check('successful transfer is marked successful',
              statuses(tid, ref), ('successful', 'successful'))
        check('  no refund', (result['refunded'], balance(wid)),
              (False, 900.0))
        check('  bank charge recorded',
              db.session.get(LocalTransferModel, tid).charge_amount, 20.0)

        # Failed: refunded and marked failed...
        tid, ref = pending_transfer(user, wallet)
        check('a pending transfer holds the money', balance(wid), 800.0)
        bank_says('failed')
        result = transfer_status.settle_transfer(tid)
        check('failed transfer is refunded', (result['refunded'],
              balance(wid)), (True, 900.0))
        check('  and marked failed', statuses(tid, ref),
              ('failed', 'failed'))

        # ...exactly once, however often it is settled again.
        transfer_status.settle_transfer(tid)
        transfer_status.settle_transfer(tid)
        check('  settling again never refunds twice', balance(wid), 900.0)

        # Reversed (status still 'successful' but reversedFlag set).
        tid, ref = pending_transfer(user, wallet)
        bank_says('successful', reversed_flag=1)
        transfer_status.settle_transfer(tid)
        check('a reversed transfer is refunded', balance(wid), 900.0)
        check('  and marked failed', statuses(tid, ref)[0], 'failed')

        # Still pending at the bank, or the bank unreachable: left alone.
        tid, ref = pending_transfer(user, wallet)
        bank_says('pending')
        transfer_status.settle_transfer(tid)
        check('still pending at the bank stays pending',
              (statuses(tid, ref)[0], balance(wid)), ('pending', 800.0))
        bank.transfer_requery = staticmethod(lambda *a, **k: None)
        transfer_status.settle_transfer(tid)
        check('bank unreachable changes nothing',
              (statuses(tid, ref)[0], balance(wid)), ('pending', 800.0))

        # Dry run reports the bank's answer without acting on it.
        bank_says('failed')
        result = transfer_status.settle_transfer(tid, apply=False)
        check('dry run reports the bank status', result['bank'], 'failed')
        check('  without refunding', (statuses(tid, ref)[0], balance(wid)),
              ('pending', 800.0))

        check('pending transfers are listed for the script',
              tid in transfer_status.pending_transfer_ids(
                  older_than_seconds=0), True)

        # The endpoint: only the owner can refresh, and it settles.
        def refresh(as_user):
            with app.test_request_context(method='POST'):
                request.current_user = {'sub': str(as_user.id)}
                response, status = LocalTransferResource.refresh_status(tid)
                return status, response.get_json()

        status, body = refresh(other)
        check("another customer's transfer is not found", status, 404)
        check('  and was not settled', statuses(tid, ref)[0], 'pending')

        status, body = refresh(user)
        check('owner refresh settles it', (status, body['data']['status'],
              body['data']['refunded']), (200, 'failed', True))
        check('  and the money is back', balance(wid), 900.0)

        # The scheduled endpoint: secret required, fails closed.
        import config
        from src.resources.transfer_settlement import (
            SECRET_HEADER, TransferSettlementResource)

        def scheduled(secret_set, header):
            config.settle_transfers_secret = secret_set
            headers = {SECRET_HEADER: header} if header is not None else {}
            with app.test_request_context(method='POST', headers=headers):
                response, status = TransferSettlementResource.settle_pending()
                return status, response.get_json()

        tid2, ref2 = pending_transfer(user, wallet)
        tid3, ref3 = pending_transfer(user, wallet)
        from datetime import datetime, timedelta
        for t in (tid2, tid3):
            db.session.get(LocalTransferModel, t).created_at = \
                datetime.now() - timedelta(minutes=5)
        db.session.commit()
        bank_says('failed')

        check('scheduled settle with no secret configured is refused',
              scheduled('', 'anything')[0], 403)
        check('  with a wrong secret is refused',
              scheduled('s3cret', 'wrong')[0], 403)
        check('  with no header is refused', scheduled('s3cret', None)[0], 403)
        check('  and none of that touched the money', balance(wid), 700.0)

        status, body = scheduled('s3cret', 's3cret')
        check('right secret settles the batch',
              (status, body['data']['refunded'], body['data']['checked']),
              (200, 2, 2))
        check('  both refunded', balance(wid), 900.0)

        # The time budget stops a long batch before gunicorn's timeout.
        tid4, _ = pending_transfer(user, wallet)
        db.session.get(LocalTransferModel, tid4).created_at = \
            datetime.now() - timedelta(minutes=5)
        db.session.commit()
        summary = transfer_status.settle_pending(budget_seconds=-1)
        check('an exhausted budget leaves the rest for the next run',
              (summary['checked'], summary['left_for_next_run']), (0, 1))

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
