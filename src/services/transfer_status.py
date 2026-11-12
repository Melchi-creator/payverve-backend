"""Settle transfers out that BellBank reported as pending.

Most BellBank transfers are 'pending' when accepted, and nothing used to look
at them again: a completed transfer stayed pending in the customer's history,
and a failed or reversed one never gave the money back.

settle_transfer() asks BellBank for the status by reference and applies it:
successful marks it so, failed or reversed refunds the wallet and marks it
failed, and anything else leaves it pending to ask again later. The transfer
row is locked and re-checked before anything changes, so however many times
this runs -- the app polling, the scheduled script, both at once -- a
transfer is refunded at most once.
"""
import time
from datetime import datetime, timedelta

import config
from ..models import LocalTransferModel, TransactionModel, WalletModel, db
from ..utilities import Cryptographer

# BellBank's words for a transfer that will not complete.
FAILED_STATUSES = ('failed', 'reversed', 'declined', 'cancelled')


def normalise_status(value, reversed_flag=None):
    """BellBank's status as one of successful, pending or failed."""
    if reversed_flag not in (None, 0, '0', False, ''):
        return 'failed'

    status = str(value or '').strip().lower()

    if status in FAILED_STATUSES:
        return 'failed'

    return 'successful' if status == 'successful' else 'pending'


def _bank_token():
    # Imported here: src.middlewares imports src.resources, which imports
    # src.services, so a module-level import closes the cycle too early.
    from ..middlewares import BellbankHelper

    return BellbankHelper.bellbank_authentication('6')


def _bank_status(reference, access_token=None):
    """(status, data) from BellBank, or (None, {}) when it cannot be asked."""
    from ..middlewares import BellbankHelper

    access_token = access_token or _bank_token()

    if not access_token:
        return None, {}

    response = BellbankHelper.transfer_requery(reference, access_token)

    if response is None or response.status_code != 200:
        return None, {}

    try:
        data = (response.json() or {}).get('data') or {}
    except ValueError:
        return None, {}

    if not data:
        return None, {}

    return normalise_status(data.get('status'), data.get('reversedFlag')), data


def expected_fee():
    """The fee held from the customer before BellBank says what it charged.

    Customers pay BellBank's transfer charge, but the exact amount only
    arrives once BellBank accepts the transfer. This much is held with the
    amount, then corrected to the real charge.
    """
    return round(float(getattr(config, 'bellbank_transfer_fee', 20) or 0), 2)


def _history_rows(transfer):
    """The customer's history rows for this transfer: 'Money Sent' and, when
    a fee was held, 'Bank Charge'. Linked by the reference in tx_ref."""
    return TransactionModel.query.filter_by(
        tx_ref=transfer.reference_number).all()


def _fee_row(transfer):
    return TransactionModel.query.filter_by(
        tx_ref=transfer.reference_number,
        transaction_type='transaction_charges').first()


def refund_locked(transfer):
    """Return a transfer's amount and fee to the wallet and mark it failed.

    The caller holds the transfer row lock and commits. Returns the total
    refunded.
    """
    wallet = WalletModel.query.filter_by(
        id=transfer.wallet_id).with_for_update().one()
    total = round(float(Cryptographer.decrypt(transfer.amount))
                  + float(transfer.charge_amount or 0), 2)
    wallet.fund = Cryptographer.encrypt(
        float(Cryptographer.decrypt(wallet.fund)) + total)
    transfer.transaction_status = 'failed'

    for row in _history_rows(transfer):
        row.status = 'failed'

    return total


def apply_charge_locked(transfer, actual_charge):
    """Correct the fee held from the customer to what BellBank charged.

    Gives back any excess, or takes the shortfall -- never more than the
    wallet holds; anything it cannot cover is logged for follow-up rather
    than driving the balance negative. The caller holds the transfer row
    lock and commits.
    """
    if actual_charge in (None, ''):
        return

    actual = round(float(actual_charge), 2)
    held = round(float(transfer.charge_amount or 0), 2)

    if actual == held:
        return

    wallet = WalletModel.query.filter_by(
        id=transfer.wallet_id).with_for_update().one()
    balance = float(Cryptographer.decrypt(wallet.fund))
    change = round(actual - held, 2)

    if change > 0 and balance < change:
        print(f'[transfer] {transfer.reference_number}: BellBank charged '
              f'₦{actual:,.2f} but only ₦{held + balance:,.2f} could be '
              f'collected; ₦{change - balance:,.2f} not recovered')
        change = round(balance, 2)

    wallet.fund = Cryptographer.encrypt(balance - change)
    collected = round(held + change, 2)
    transfer.charge_amount = collected

    fee_row = _fee_row(transfer)

    if fee_row is not None:
        fee_row.amount = Cryptographer.encrypt(f'{collected:.2f}')


def settle_transfer(transfer_id, apply=True, access_token=None):
    """Bring one transfer in line with BellBank. Returns a dict describing
    what was found and done: {'reference', 'was', 'bank', 'now', 'refunded'}.

    With apply=False nothing is written; the bank's answer is still reported.
    """
    transfer = db.session.get(LocalTransferModel, transfer_id)

    if transfer is None:
        return None

    result = {'reference': transfer.reference_number,
              'was': transfer.transaction_status, 'bank': None,
              'now': transfer.transaction_status, 'refunded': False}

    if transfer.transaction_status != 'pending':
        return result

    bank_status, data = _bank_status(transfer.reference_number, access_token)
    result['bank'] = bank_status

    if bank_status in (None, 'pending') or not apply:
        db.session.rollback()
        return result

    # Re-read under a lock: another worker may have settled it while the
    # bank was being asked.
    transfer = LocalTransferModel.query.filter_by(
        id=transfer_id).with_for_update().one()

    if transfer.transaction_status != 'pending':
        db.session.rollback()
        result['now'] = transfer.transaction_status
        return result

    if bank_status == 'failed':
        refund_locked(transfer)
        result['refunded'] = True
    else:
        apply_charge_locked(transfer, data.get('charge'))
        transfer.transaction_status = bank_status

        for row in _history_rows(transfer):
            row.status = bank_status

    db.session.commit()
    result['now'] = bank_status

    print(f'[transfer] {transfer.reference_number} settled: {bank_status}'
          + (' (refunded)' if result['refunded'] else ''))

    _notify(transfer, bank_status)

    return result


def _notify(transfer, status):
    """Tell the customer; a notification failure never undoes the settle."""
    from ..resources.notification import NotificationResource

    try:
        amount = float(Cryptographer.decrypt(transfer.amount))
        fee = float(transfer.charge_amount or 0)

        if status == 'failed':
            NotificationResource.store_and_push(
                title='Transfer Failed',
                body=f'Your transfer of ₦{amount:,.2f} to '
                     f'{transfer.recipient_name} did not go through. '
                     f'The ₦{amount + fee:,.2f} (including the ₦{fee:,.2f} '
                     f'fee) is back in your wallet.',
                user_id=transfer.user_id,
                data={'type': 'wallet_credit',
                      'amount': f'{amount + fee:.2f}'},
            )
        elif status == 'successful':
            NotificationResource.store_nofication(
                title='Transfer Successful',
                body=f'₦{amount:,.2f} has reached {transfer.recipient_name}.',
                user_id=transfer.user_id,
            )
    except Exception as e:  # noqa: BLE001
        print(f'[transfer] settle notification failed for '
              f'{transfer.reference_number}: {type(e).__name__}: {e}')


def pending_transfer_ids(older_than_seconds=60, limit=200):
    """Pending transfers old enough that the bank should know their fate."""
    cutoff = datetime.now() - timedelta(seconds=older_than_seconds)

    return [row.id for row in LocalTransferModel.query.filter(
        LocalTransferModel.transaction_status == 'pending',
        LocalTransferModel.created_at <= cutoff,
    ).order_by(LocalTransferModel.created_at).limit(limit).all()]


def settle_pending(older_than_seconds=60, limit=25, budget_seconds=20):
    """Settle a batch of pending transfers within a time budget.

    For the scheduled caller: gunicorn kills a request after 30 seconds, so
    this stops starting new transfers once the budget is spent and leaves the
    rest for the next run. One BellBank token serves the whole batch.
    """
    started = time.monotonic()
    summary = {'checked': 0, 'successful': 0, 'failed': 0, 'refunded': 0,
               'still_pending': 0, 'errors': 0, 'left_for_next_run': 0}
    ids = pending_transfer_ids(older_than_seconds, limit)
    access_token = _bank_token() if ids else None

    for index, transfer_id in enumerate(ids):
        if time.monotonic() - started > budget_seconds:
            summary['left_for_next_run'] = len(ids) - index
            break

        try:
            result = settle_transfer(transfer_id, access_token=access_token)
        except Exception as e:  # noqa: BLE001 - one bad row must not stop the rest
            db.session.rollback()
            summary['errors'] += 1
            print(f'[transfer] settle failed for {transfer_id}: '
                  f'{type(e).__name__}: {e}')
            continue

        summary['checked'] += 1
        now = result['now']

        if result['refunded']:
            summary['refunded'] += 1
        if now == 'successful':
            summary['successful'] += 1
        elif now == 'failed':
            summary['failed'] += 1
        else:
            summary['still_pending'] += 1

    return summary
