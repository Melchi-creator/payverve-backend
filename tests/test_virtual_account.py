"""Wallets must carry a real BellBank account number, or none at all.

Wallets were created with RandomGenerator.sim_account_number(). Nothing routed
to that number -- the collection webhook resolves deposits by the virtual
account, so every real BellBank notification failed to find a wallet -- and the
customer was told it was theirs.

Account details live on virtual_account_numbers here; migration 2129b3c36f79
dropped them from wallets.

Run:  ENV=development PYTHONPATH=. python tests/test_virtual_account.py
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

# src.middlewares imports src.resources, which imports src.middlewares back.
# Loading resources first is the order that resolves; importing middlewares
# cold raises ImportError on PaystackHelper.
import src.resources  # noqa: E402,F401
import src.middlewares as middlewares  # noqa: E402

from src.models import (CurrencyModel, UserModel,  # noqa: E402
                        VirtualAccountNumberModel, WalletModel, db)
from src.services import registration, virtual_account  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

REAL_ACCOUNT = '9901234567'
_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<48} got={got!r} want={want!r}")


class _BankResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def stub_bank(response):
    """Replace the BellBank calls the service makes."""
    middlewares.BellbankHelper.bellbank_authentication = \
        staticmethod(lambda *a, **k: 'stub-token')
    middlewares.BellbankHelper.bellbank_virtual_account = \
        staticmethod(lambda *a, **k: response)


def seed():
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
    return ngn, user


def main():
    with app.app_context():
        ngn, user = seed()

        wallet = registration.stage_ngn_wallet(user.id, ngn.id)
        db.session.commit()

        check('wallet starts with no virtual account',
              VirtualAccountNumberModel.query.count(), 0)
        check('  and is inactive', wallet.is_active, False)

        # No bvn -> refused, and nothing invented.
        stub_bank(_BankResponse(200, {'data': {'accountNumber': REAL_ACCOUNT}}))
        try:
            virtual_account.provision_ngn_virtual_account(
                user, wallet, None, ' 12 Broad St', ngn.id)
            check('missing bvn refused', 'no error', 'RegistrationError')
        except registration.RegistrationError as e:
            check('missing bvn refused', e.code, 400)
        check('  still no virtual account',
              VirtualAccountNumberModel.query.count(), 0)

        # Bank refuses -> nothing written.
        stub_bank(_BankResponse(400, {'message': 'invalid bvn'}))
        try:
            virtual_account.provision_ngn_virtual_account(
                user, wallet, '22222222222', '12 Broad St', ngn.id)
            check('bank rejection surfaced', 'no error', 'RegistrationError')
        except registration.RegistrationError as e:
            check('bank rejection surfaced', (e.code, e.message),
                  (400, 'invalid bvn'))
        db.session.rollback()
        check('  still no virtual account',
              VirtualAccountNumberModel.query.count(), 0)

        # Bank returns no number -> refuse rather than store a blank.
        stub_bank(_BankResponse(200, {'data': {}}))
        try:
            virtual_account.provision_ngn_virtual_account(
                user, wallet, '22222222222', '12 Broad St', ngn.id)
            check('empty bank response refused', 'no error', 'RegistrationError')
        except registration.RegistrationError as e:
            check('empty bank response refused', e.code, 502)
        db.session.rollback()

        # Success.
        stub_bank(_BankResponse(200, {'data': {
            'accountNumber': REAL_ACCOUNT,
            'externalReference': 'bb-ext-1',
            'bankName': 'bellbank microfinance bank',
        }}))
        virtual_account.provision_ngn_virtual_account(
            user, wallet, '22222222222', '12 Broad St', ngn.id)
        db.session.commit()

        issued = VirtualAccountNumberModel.query.first()
        check('real account number issued',
              issued.account_number, REAL_ACCOUNT)
        check('  wallet activated', wallet.is_active, True)
        check('  bank name recorded', issued.account_bank_name,
              'bellbank microfinance bank')
        check('  external reference recorded', issued.reference, 'bb-ext-1')
        check('  exactly one virtual account row',
              VirtualAccountNumberModel.query.count(), 1)
        check('  expiry null for a static account',
              VirtualAccountNumberModel.query.first().account_expiration_datetime,
              None)

        # The webhook resolves deposits through exactly this call.
        from src.middlewares import BellbankHelper
        found = BellbankHelper.wallet_for_virtual_account(REAL_ACCOUNT)
        check('deposit lookup finds the wallet',
              found is not None and str(found.id) == str(wallet.id), True)
        check('  and an unknown account resolves to nothing',
              BellbankHelper.wallet_for_virtual_account('0000000000'), None)

        # Re-provisioning is a no-op, not a second bank call or a duplicate row.
        def _explode(*a, **k):
            raise AssertionError('bank called again for a provisioned wallet')

        middlewares.BellbankHelper.bellbank_virtual_account = staticmethod(_explode)
        virtual_account.provision_ngn_virtual_account(
            user, wallet, '22222222222', '12 Broad St', ngn.id)
        db.session.commit()
        check('re-provision is a no-op',
              VirtualAccountNumberModel.query.first().account_number,
              REAL_ACCOUNT)
        check('  no duplicate virtual account row',
              VirtualAccountNumberModel.query.count(), 1)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
