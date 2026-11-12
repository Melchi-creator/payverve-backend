"""
webhook_retry.py

Scheduled resend of merchant webhooks.
"""

from flask import Blueprint

from ..resources import WebhookRetryResource

WebhookRetryBlueprint = Blueprint("webhook_retry", __name__)

# NOT jwt_required: the caller is the scheduled job, not a customer. It is
# authenticated by WEBHOOK_RETRY_SECRET inside the resource, which fails
# closed when the secret is unset.
WebhookRetryBlueprint.route(
    "/internal/retry-webhooks",
    methods=['POST'])(WebhookRetryResource.retry_pending)
