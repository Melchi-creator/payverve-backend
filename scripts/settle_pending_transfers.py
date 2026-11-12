"""Settle every transfer out that is still pending.

Asks BellBank for each pending transfer's status by reference. Successful
ones are marked so; failed or reversed ones are refunded to the wallet and
marked failed; ones the bank still has as pending are left for the next run.
Each transfer is locked and re-checked before it changes, so this can run on
a schedule alongside the app without ever refunding twice.

DRY RUN BY DEFAULT: reports what BellBank says and changes nothing until
--apply is passed.

    python scripts/settle_pending_transfers.py
    python scripts/settle_pending_transfers.py --apply
    python scripts/settle_pending_transfers.py --apply --older-than 300 --limit 50

Run it against the sandbox with ENV_FILE=.env.sandbox, as the app.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsgi import payverve as app  # noqa: E402
from src.services import transfer_status  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true',
                        help='refund failed transfers and update statuses')
    parser.add_argument('--older-than', type=int, default=60,
                        help='only transfers pending at least this many '
                             'seconds (default 60)')
    parser.add_argument('--limit', type=int, default=200)
    args = parser.parse_args()

    print('MODE: ' + ('APPLY' if args.apply else 'dry run - nothing changes'))

    counts = {}

    with app.app_context():
        ids = transfer_status.pending_transfer_ids(args.older_than, args.limit)
        print(f'{len(ids)} pending transfer(s)')

        for transfer_id in ids:
            try:
                result = transfer_status.settle_transfer(
                    transfer_id, apply=args.apply)
            except Exception as e:  # noqa: BLE001 - keep going
                print(f'  {transfer_id}: error {type(e).__name__}: {e}')
                counts['error'] = counts.get('error', 0) + 1
                continue

            bank = result['bank'] or 'no answer'
            outcome = result['now'] if args.apply else f'would be {bank}'
            print(f"  {result['reference']}: bank says {bank} -> {outcome}"
                  + (' (refunded)' if result['refunded'] else ''))
            counts[bank] = counts.get(bank, 0) + 1

    print('summary:', counts or 'nothing to do')
    return 0


if __name__ == '__main__':
    sys.exit(main())
