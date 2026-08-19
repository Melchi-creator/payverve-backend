"""Give existing wallets a real BellBank virtual account.

Wallets created before provisioning was wired up have no row in
virtual_account_numbers, so nothing routes to them: the collection webhook
resolves a deposit by looking the virtual account up in that table. Those
customers cannot receive money.

Two populations need this:

  * wallets that never had an account at all, and
  * wallets whose owner completed KYC while other_wallet() was assigning
    own_wallet.account_number -- a column migration 2129b3c36f79 had already
    dropped. BellBank issued a real account for them and Payverve recorded
    nothing. Re-provisioning repairs those: BellBank keys the request on the
    customer's own details, so it returns the same account it issued before.

Accounts issued by another provider are reported, not touched. Flutterwave
sandbox ones show up as 'Mock Bank'; deposits to them do not arrive through the
BellBank webhook, but replacing one moves where a customer's money lands, so
that is a decision for a person rather than this script.

DRY RUN BY DEFAULT. Nothing is written and the bank is never called until
--apply is passed.

    # see what would happen
    python scripts/backfill_virtual_accounts.py

    # one user first
    python scripts/backfill_virtual_accounts.py --email someone@example.com --apply

    # then the rest, gently
    python scripts/backfill_virtual_accounts.py --apply --delay 1 --limit 50

Each wallet is committed on its own, so the run is resumable: re-running skips
whatever already succeeded.
"""
import argparse
import sys
import time

import server  # builds the Flask app and binds the database
from src.models import (CurrencyModel, KYCModel, UserModel,
                        VirtualAccountNumberModel, WalletModel, db)
from src.services import registration, virtual_account


def existing_account(wallet):
    """The virtual account on record for this wallet, whoever issued it."""
    return VirtualAccountNumberModel.query.filter_by(
        user_id=wallet.user_id, currency_id=wallet.currency_id).first()


def is_bellbank(virtual_account):
    """Whether an account on record was issued by BellBank.

    Accounts from other providers are already in this table -- Flutterwave
    sandbox ones show up as 'Mock Bank' -- and deposits to them do not arrive
    through the BellBank webhook. They are reported separately rather than
    counted as done, because replacing one moves where a customer's money
    lands and is not a decision this script should make quietly.
    """
    name = (virtual_account.account_bank_name or '').lower()
    return 'bell' in name


def kyc_details(user_id):
    """The bvn and address BellBank needs, or (None, None)."""
    kyc = KYCModel.query.filter_by(user_id=user_id).first()

    if not kyc or not kyc.bvn or not kyc.address:
        return None, None

    return kyc.bvn, kyc.address


def main():
    parser = argparse.ArgumentParser(
        description='Provision real BellBank virtual accounts for existing '
                    'wallets. Dry run unless --apply is given.')
    parser.add_argument('--apply', action='store_true',
                        help='actually call the bank and write the results')
    parser.add_argument('--limit', type=int,
                        help='stop after this many wallets')
    parser.add_argument('--email',
                        help='only this user, by email address')
    parser.add_argument('--delay', type=float, default=0.0,
                        help='seconds to wait between bank calls')
    args = parser.parse_args()

    with server.server.app_context():
        ngn = CurrencyModel.query.filter_by(short_code='ngn').first()

        if not ngn:
            print('no ngn currency configured; nothing to do')
            return 1

        query = WalletModel.query.filter_by(currency_id=ngn.id)

        if args.email:
            user = UserModel.query.filter_by(
                email_address=args.email).first()

            if not user:
                print(f'no user with email {args.email}')
                return 1

            query = query.filter_by(user_id=user.id)

        wallets = query.order_by(WalletModel.created_at).all()

        print('DRY RUN -- nothing will be written' if not args.apply
              else 'APPLYING')
        print(f'ngn wallets found: {len(wallets)}\n')

        tally = {'already on bellbank': 0, 'on another provider': 0,
                 'provisioned': 0, 'waiting on kyc': 0, 'failed': 0}
        touched = 0

        for wallet in wallets:
            if args.limit is not None and touched >= args.limit:
                print(f'\nstopping at --limit {args.limit}')
                break

            user = UserModel.query.filter_by(id=wallet.user_id).first()

            if not user:
                print(f'  SKIP    wallet {wallet.id}: no user')
                tally['failed'] += 1
                continue

            who = user.email_address
            on_record = existing_account(wallet)

            if on_record and is_bellbank(on_record):
                tally['already on bellbank'] += 1
                continue

            if on_record:
                tally['on another provider'] += 1
                print(f'  OTHER   {who}: {on_record.account_number} with '
                      f'{on_record.account_bank_name} (status '
                      f'{on_record.status}) -- deposits to it do not arrive '
                      f'through the BellBank webhook')
                continue

            bvn, address = kyc_details(wallet.user_id)

            if not bvn or not address:
                tally['waiting on kyc'] += 1
                print(f'  WAIT    {who}: no bvn/address on kyc yet')
                continue

            touched += 1

            if not args.apply:
                print(f'  WOULD PROVISION {who}')
                continue

            try:
                virtual_account.provision_ngn_virtual_account(
                    user, wallet, bvn, address, ngn.id)
                db.session.commit()

                issued = existing_account(wallet)
                tally['provisioned'] += 1
                print(f'  OK      {who}: account number '
                      f'{issued.account_number if issued else "?"}')
            except registration.RegistrationError as e:
                db.session.rollback()
                tally['failed'] += 1
                print(f'  FAILED  {who}: {e.code} {e.message}')
            except Exception as e:
                db.session.rollback()
                tally['failed'] += 1
                print(f'  ERROR   {who}: {type(e).__name__}: {e}')

            if args.delay:
                time.sleep(args.delay)

        print('\n--- summary ---')
        for label, count in tally.items():
            print(f'  {label:<18} {count}')

        if not args.apply:
            print('\ndry run only. re-run with --apply to make these changes.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
