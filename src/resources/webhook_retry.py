"""
src/resources/webhook_retry.py

Resending merchant webhooks a shop's server did not accept.

Not for customers or the app: it is authenticated by WEBHOOK_RETRY_SECRET,
sent in the X-Webhook-Retry-Secret header, and fails closed when that is unset
-- the same shape as the transfer settlement job.
"""
from hmac import compare_digest

from flask import jsonify, request

import config
from ..services import merchant_webhook

SECRET_HEADER = 'X-Webhook-Retry-Secret'


class WebhookRetryResource:
    """  """

    @staticmethod
    def retry_pending():
        expected = (getattr(config, 'webhook_retry_secret', '') or '').strip()
        sent = (request.headers.get(SECRET_HEADER) or '').strip()

        if not expected:
            print('[webhook] WEBHOOK_RETRY_SECRET is not set; rejecting')
            return jsonify({'code': 403, 'status_message': 'forbidden',
                            'message': 'webhook retry is not enabled'}), 403

        if not sent or not compare_digest(sent, expected):
            print(f'[webhook] rejected: bad or missing {SECRET_HEADER}')
            return jsonify({'code': 403, 'status_message': 'forbidden',
                            'message': 'webhook retry is not enabled'}), 403

        tally = merchant_webhook.retry_due(limit=50)
        print(f'[webhook] retry run: {tally}')

        return jsonify({'code': 200, 'status_message': 'success',
                        'data': tally}), 200
