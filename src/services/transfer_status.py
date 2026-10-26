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
from datetime import datetime, timedelta

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


def _bank_status(reference):
    """(status, data) from BellBank, or (None, {}) when it cannot be asked."""
    # Imported here: src.middlewares imports src.resources, which imports
    # src.services, so a module-level import closes the cycle too early.
    from ..middlewares import BellbankHelper

    access_token = BellbankHelper.bellbank_authentication('6')

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


def _history_for(transfer):
    """The customer's 'Money Sent' history row for this transfer, if linked."""
    return TransactionModel.query.filter_by(
        tx_ref=transfer.reference_number,
        transaction_type='domestic_transfer').first()


def settle_transfer(transfer_id, apply=True):
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

    bank_status, data = _bank_status(transfer.reference_number)
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

    history = _history_for(transfer)

    if data.get('charge') not in (None, ''):
        transfer.charge_amount = float(data['charge'])

    if bank_status == 'failed':
        wallet = WalletModel.query.filter_by(
            id=transfer.wallet_id).with_for_update().one()
        amount = float(Cryptographer.decrypt(transfer.amount))
        wallet.fund = Cryptographer.encrypt(
            float(Cryptographer.decrypt(wallet.fund)) + amount)
        result['refunded'] = True

    transfer.transaction_status = bank_status

    if history is not None:
        history.status = bank_status

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

        if status == 'failed':
            NotificationResource.store_and_push(
                title='Transfer Failed',
                body=f'Your transfer of ₦{amount:,.2f} to '
                     f'{transfer.recipient_name} did not go through. '
                     f'The money is back in your wallet.',
                user_id=transfer.user_id,
                data={'type': 'wallet_credit', 'amount': f'{amount:.2f}'},
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
