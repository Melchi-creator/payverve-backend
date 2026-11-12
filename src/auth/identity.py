"""Who is calling, and may they touch this record.

jwt_required establishes that the bearer token is valid and that its subject is
a real customer or admin. It stops there: it records no role and checks no
ownership, and it is the only auth decorator in this codebase. So every handler
that takes an id from the URL or the request body was authorising on a value
the caller supplied -- which is how one signed-in customer could read another
customer's BVN, and how POST /local-transfers could be pointed at somebody
else's wallet.

These helpers are the missing half. A handler that acts on a specific record
must establish the caller from the token, never from the request.
"""
from functools import wraps

from flask import jsonify, request

from ..models import AdminModel


def caller_id():
    """The authenticated subject id, as jwt_required recorded it."""
    current = getattr(request, 'current_user', None) or {}
    return str(current.get('sub') or '')


def caller_is_admin():
    """Whether the caller is an admin rather than a customer."""
    caller = caller_id()

    if not caller:
        return False

    return AdminModel.query.filter_by(id=caller).first() is not None


def owns(subject_id):
    """Whether the caller may act on records belonging to subject_id.

    Admins pass for everything; a customer passes only for their own id.
    """
    if caller_is_admin():
        return True

    caller = caller_id()

    return bool(caller) and str(subject_id) == caller


def forbidden(message='you cannot act on another customer record'):
    """The refusal to return when ownership fails on a write."""
    return jsonify({
        'code': 403,
        'status_message': 'forbidden',
        'message': message
    }), 403


def not_found(message='no record was found'):
    """The refusal to return when ownership fails on a read.

    404 rather than 403: a 403 confirms the record exists, which is the thing
    an enumerating caller is trying to learn.
    """
    return jsonify({
        'code': 404,
        'status_message': 'data not found',
        'message': message
    }), 404


def admin_required(f):
    """Restrict a handler to admins. Compose inside jwt_required:

        jwt_required(admin_required(Resource.read_all))

    jwt_required runs first and populates request.current_user, so this can
    rely on it having been set.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not caller_is_admin():
            # Not 403: an endpoint a customer has no business knowing about
            # should not advertise that it exists and is admin-only.
            return not_found('no record was found')

        return f(*args, **kwargs)

    return decorated
