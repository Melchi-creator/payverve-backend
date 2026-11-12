"""A customer's BVN must not be readable by anybody else, or stored in the clear.

kycs.bvn and kycs.nin were plaintext columns, and GET /kycs ran
KYCModel.query.all() behind nothing but jwt_required -- which admits any signed-in
customer and performs no role or ownership check. One request returned every
customer's bvn, nin, address and selfie. GET /kycs/<id> had no ownership check
either, and PUT /kycs/<id> trusted the user_id in the path, so a customer could
write a bvn onto someone else's record -- permanently, since bvn can be set only
once.

Run:  ENV=development PYTHONPATH=. python tests/test_kyc_identifier_privacy.py
"""
import sys
import uuid
from datetime import date

# The resources pass UUIDs through as strings. Postgres accepts that; SQLite's
# Uuid bind processor demands a uuid.UUID. Shim it so these tests exercise the
# real code path rather than a dialect quirk.
from sqlalchemy import types as _satypes

_orig_bind_processor = _satypes.Uuid.bind_processor


def _tolerant_bind_processor(self, dialect):
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

from flask import Flask, request  # noqa: E402

import src.resources  # noqa: F401,E402  (resources before middlewares)
from src.models import KYCModel, UserModel, db  # noqa: E402
from src.resources.kyc import KYCResource  # noqa: E402
from src.utilities import (decrypt_identifier, encrypt_identifier,  # noqa: E402
                           hash_identifier)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

MY_BVN = '22222222222'
THEIR_BVN = '33333333333'

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<54} got={got!r} want={want!r}")


def make_user(name):
    user = UserModel(first_name=name, last_name='Test',
                     email_address=f'{name}@example.com', username=name,
                     mobile_number=f'80{abs(hash(name)) % 1000000000:09d}',
                     user_code=name.upper(), gender='male',
                     date_of_birth=date(1990, 1, 1))
    user.set_password('Abcdef1!x')
    db.session.add(user)
    db.session.commit()
    return user


def make_kyc(user, bvn):
    kyc = KYCModel(user_id=user.id, tier=1,
                   bvn=encrypt_identifier(bvn), bvn_hash=hash_identifier(bvn),
                   bvn_present=True, full_name_present=True,
                   phone_number_present=True)
    db.session.add(kyc)
    db.session.commit()
    return kyc


def as_caller(user_id, fn, *args, **kwargs):
    """Invoke a resource the way jwt_required leaves the request."""
    with app.test_request_context(json={}):
        request.current_user = {'sub': str(user_id), 'jti': 'x'}
        result = fn(*args, **kwargs)
    return result


def body_of(result):
    response = result[0] if isinstance(result, tuple) else result
    return response.get_json()


def status_of(result):
    return result[1] if isinstance(result, tuple) else 200


def main():
    with app.app_context():
        db.create_all()

        me = make_user('me')
        them = make_user('them')
        my_kyc = make_kyc(me, MY_BVN)
        their_kyc = make_kyc(them, THEIR_BVN)

        # At rest: the column holds ciphertext, not the identifier.
        stored = db.session.get(KYCModel, my_kyc.id).bvn
        check('stored value is not the plaintext bvn', stored == MY_BVN, False)
        check('  and round-trips back', decrypt_identifier(stored), MY_BVN)
        check('  Fernet, so ciphertext cannot be unique-constrained',
              encrypt_identifier(MY_BVN) == encrypt_identifier(MY_BVN), False)
        check('  which is why the hash is deterministic',
              hash_identifier(MY_BVN) == hash_identifier(MY_BVN), True)

        # read_all as a customer: own record only, and no identifiers in it.
        result = as_caller(me.id, KYCResource.read_all)
        rows = body_of(result)['data']
        check('read_all returns only my own record', len(rows), 1)
        check('  it is mine', str(rows[0]['user_id']), str(me.id))
        check('  no bvn field at all', 'bvn' in rows[0], False)
        check('  no nin field at all', 'nin' in rows[0], False)
        check('  bvn_present still tells the client what it needs',
              rows[0]['bvn_present'], True)

        # read_one on somebody else's record.
        result = as_caller(me.id, KYCResource.read_one, id=their_kyc.id)
        check('read_one on another record is refused', status_of(result), 404)
        check('  and my own is still readable',
              status_of(as_caller(me.id, KYCResource.read_one,
                                  id=my_kyc.id)), 200)
        check('  without leaking the identifier',
              'bvn' in body_of(as_caller(me.id, KYCResource.read_one,
                                         id=my_kyc.id))['data'], False)

        # update against somebody else's user_id.
        with app.test_request_context(json={'address': '1 Elsewhere St'}):
            request.current_user = {'sub': str(me.id), 'jti': 'x'}
            result = KYCResource.update(id=them.id, bvn=None, selfie=None,
                                        nin=None, address='1 Elsewhere St')
        check('update on another customer is refused', status_of(result), 403)
        check('  their record is untouched',
              db.session.get(KYCModel, their_kyc.id).address, None)

        # A duplicate bvn is still rejected, now via the hash...
        fresh = make_user('fresh')
        db.session.add(KYCModel(user_id=fresh.id, tier=0,
                                full_name_present=True,
                                phone_number_present=True))
        db.session.commit()

        with app.test_request_context(json={'bvn': MY_BVN}):
            request.current_user = {'sub': str(fresh.id), 'jti': 'x'}
            result = KYCResource.update(id=fresh.id, bvn=MY_BVN, selfie=None,
                                        nin=None, address=None)
        check('a bvn already on file is rejected', status_of(result), 409)
        # ...without confirming that it is registered, which would make this
        # endpoint an oracle for whether a given person banks here.
        message = (body_of(result).get('message') or '').lower()
        check('  message does not confirm it is registered',
              'already' in message, False)

    print()
    if _failures:
        print(f'{len(_failures)} FAILED: ' + ', '.join(_failures))
        return 1
    print('ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
