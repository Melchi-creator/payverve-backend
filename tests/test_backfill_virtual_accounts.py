"""The backfill must provision the right wallets and leave the rest alone.

Exercises the same predicates scripts/backfill_virtual_accounts.py uses, against
a real database, so a mistake in "who needs an account" shows up here rather
than against live customers.

Run:  ENV=development PYTHONPATH=. python tests/test_backfill_virtual_accounts.py
"""
import os
import sys
import uuid
from datetime import date

from sqlalchemy import types as _satypes

_orig_bind_processor = _satypes.Uuid.bind_processor


def _tolerant_bind_processor(self, dialect):
    """Postgres accepts UUID strings; SQLite demands objects."""
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

import src.resources  # noqa: E402,F401  (load order: resources before middlewares)
import src.middlewares as middlewares  # noqa: E402

from src.models import (CurrencyModel, KYCModel, UserModel,  # noqa: E402
                        VirtualAccountNumberModel, WalletModel, db)
from src.services import registration, virtual_account  # noqa: E402
from src.utilities import Cryptographer  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []
_issued = iter(['9900000001', '9900000002', '9900000003'])


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<46} got={got!r} want={want!r}")


class _BankResponse:
    status_code = 200

    @staticmethod
    def json():
        return {'data': {'accountNumber': next(_issued),
                         'externalReference': f'ext-{uuid.uuid4().hex[:6]}'}}


def stub_bank():
    middlewares.BellbankHelper.bellbank_authentication = \
        staticmethod(lambda *a, **k: 'stub-token')
    middlewares.BellbankHelper.bellbank_virtual_account = \
        staticmethod(lambda *a, **k: _BankResponse())


_seq = iter(range(1, 99))


def make_user(ngn, tag, with_kyc):
    n = next(_seq)
    user = UserModel(first_name=tag.title(), last_name='Test',
                     email_address=f'{tag}@example.com', username=tag,
                     mobile_number=f'80100000{n:02d}',
                     user_code=f'C{tag[:4].upper()}', gender='male',
                     date_of_birth=date(1990, 1, 1), customer_code=f'cust_{tag}')
    user.set_password('Abcdef1!x')
    db.session.add(user)
    db.session.commit()

    wallet = registration.stage_ngn_wallet(user.id, ngn.id)
    db.session.commit()

    if with_kyc:
        db.session.add(KYCModel(user_id=user.id, bvn=f'{abs(hash(tag)) % 10**11:011d}',
                                address='12 Broad Street, Lagos', tier=3))
        db.session.commit()

    return user, wallet


# the predicates the script uses
def existing_account(wallet):
    return VirtualAccountNumberModel.query.filter_by(
        user_id=wallet.user_id, currency_id=wallet.currency_id).first()


def is_bellbank(virtual_account):
    return 'bell' in (virtual_account.account_bank_name or '').lower()


def kyc_details(user_id):
    kyc = KYCModel.query.filter_by(user_id=user_id).first()
    if not kyc or not kyc.bvn or not kyc.address:
        return None, None
    return kyc.bvn, kyc.address


def run_backfill(ngn, apply_changes):
    """Mirrors the script's loop."""
    tally = {'already on bellbank': 0, 'on another provider': 0,
             'provisioned': 0, 'waiting on kyc': 0, 'failed': 0}

    for wallet in WalletModel.query.filter_by(currency_id=ngn.id).all():
        user = UserModel.query.filter_by(id=wallet.user_id).first()
        on_record = existing_account(wallet)

        if on_record and is_bellbank(on_record):
            tally['already on bellbank'] += 1
            continue

        if on_record:
            tally['on another provider'] += 1
            continue

        bvn, address = kyc_details(wallet.user_id)

        if not bvn or not address:
            tally['waiting on kyc'] += 1
            continue

        if not apply_changes:
            continue

        try:
            virtual_account.provision_ngn_virtual_account(
                user, wallet, bvn, address, ngn.id)
            db.session.commit()
            tally['provisioned'] += 1
        except registration.RegistrationError:
            db.session.rollback()
            tally['failed'] += 1

    return tally


def main():
    stub_bank()

    with app.app_context():
        db.create_all()
        ngn = CurrencyModel(name='naira', short_code='ngn', country='nigeria')
        db.session.add(ngn)
        db.session.commit()

        ready, ready_wallet = make_user(ngn, 'ready', with_kyc=True)
        waiting, _ = make_user(ngn, 'waiting', with_kyc=False)
        done, done_wallet = make_user(ngn, 'done', with_kyc=True)

        # 'done' already has an account, as if provisioned earlier.
        virtual_account.provision_ngn_virtual_account(
            done, done_wallet, '11111111111', '1 Old Road', ngn.id)
        db.session.commit()
        before_done = existing_account(done_wallet).account_number

        # A wallet already carrying a Flutterwave sandbox account.
        other, other_wallet_row = make_user(ngn, 'other', with_kyc=True)
        db.session.add(VirtualAccountNumberModel(
            virtual_account_id='flw-1', account_number='5550000001',
            reference='flw-ref-1', account_bank_name='Mock Bank',
            account_type='static', status='limited', customer_code='cust_other',
            currency_ticker='NGN', is_active=True, user_id=other.id,
            currency_id=ngn.id))
        db.session.commit()

        check('setup: accounts on record', VirtualAccountNumberModel.query.count(), 2)

        # Dry run must change nothing.
        dry = run_backfill(ngn, apply_changes=False)
        check('dry run provisions nothing', VirtualAccountNumberModel.query.count(), 2)
        check('  counts the one already done', dry['already on bellbank'], 1)
        check('  counts the one waiting on kyc', dry['waiting on kyc'], 1)
        check('  counts the one on another provider',
              dry['on another provider'], 1)

        # Apply.
        applied = run_backfill(ngn, apply_changes=True)
        check('apply provisions the ready wallet', applied['provisioned'], 1)
        check('  skips the one already done', applied['already on bellbank'], 1)
        check('  leaves the kyc-less one alone', applied['waiting on kyc'], 1)
        check('  nothing failed', applied['failed'], 0)
        check('  reports rather than replaces another provider',
              applied['on another provider'], 1)
        check('  mock bank account left untouched',
              existing_account(other_wallet_row).account_number, '5550000001')

        check('ready wallet now has an account',
              existing_account(ready_wallet) is not None, True)
        check('  and is active', ready_wallet.is_active, True)
        check('waiting wallet still has none',
              existing_account(WalletModel.query.filter_by(
                  user_id=waiting.id).first()), None)
        check('already-done account untouched',
              existing_account(done_wallet).account_number, before_done)
        check('total accounts on record', VirtualAccountNumberModel.query.count(), 3)

        # Re-running is safe.
        second = run_backfill(ngn, apply_changes=True)
        check('re-run provisions nothing new', second['provisioned'], 0)
        check('  everyone provisioned is skipped', second['already on bellbank'], 2)
        check('  accounts unchanged', VirtualAccountNumberModel.query.count(), 3)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
