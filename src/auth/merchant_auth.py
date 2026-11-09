"""Authenticating a shop's server by its secret key.

A merchant endpoint is not called by a person with a Payverve session, so
jwt_required does not apply -- the same reason the BellBank webhook could not
use it. The shop presents its secret key instead.

The key is matched on its keyed hash, so the plaintext never exists in the
database and a stolen copy cannot be used to raise charges.
"""
from functools import wraps

from flask import jsonify, request

from ..services.checkout import merchant_for_secret

HEADER = 'Authorization'
SCHEME = 'Bearer '


def _refused():
    # Deliberately identical for a missing, malformed, unknown or deactivated
    # key: distinguishing them tells a caller which keys exist.
    return jsonify({
        'code': 401,
        'status_message': 'unauthorised',
        'message': 'a valid merchant secret key is required'
    }), 401


def merchant_required(f):
    """Resolve the merchant from the secret key, or refuse.

    The merchant is passed to the handler as `merchant`, so a handler can
    never act on a merchant id taken from the URL or body -- the caller only
    ever reaches the merchant their own key belongs to.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get(HEADER, '')

        if not header.startswith(SCHEME):
            return _refused()

        merchant = merchant_for_secret(header[len(SCHEME):])

        if not merchant:
            return _refused()

        kwargs['merchant'] = merchant
        return f(*args, **kwargs)

    return decorated
