"""Scheduled settling of pending transfers, for the GitHub Action.

Not for customers or the app: it is authenticated by SETTLE_TRANSFERS_SECRET,
sent in the X-Settle-Secret header, and fails closed when that is unset.
"""
from hmac import compare_digest

from flask import jsonify, request

import config
from ..services import transfer_status

SECRET_HEADER = 'X-Settle-Secret'


class TransferSettlementResource:
    """  """

    @staticmethod
    def settle_pending():
        expected = (getattr(config, 'settle_transfers_secret', '') or '').strip()
        sent = (request.headers.get(SECRET_HEADER) or '').strip()

        if not expected:
            print('[settle] SETTLE_TRANSFERS_SECRET is not set; rejecting')
            return jsonify({'code': 403, 'status_message': 'forbidden',
                            'message': 'settlement is not enabled'}), 403

        if not sent or not compare_digest(sent, expected):
            print(f'[settle] rejected: bad or missing {SECRET_HEADER}')
            return jsonify({'code': 403, 'status_message': 'forbidden',
                            'message': 'not allowed'}), 403

        summary = transfer_status.settle_pending()
        print(f'[settle] {summary}')

        return jsonify({'code': 200, 'status_message': 'success',
                        'data': summary}), 200
