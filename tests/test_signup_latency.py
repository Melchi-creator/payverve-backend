"""Signup must answer quickly even when the mail provider is slow.

Both Mailtrap sends used to run inline after the commit, each bounded at
MAILTRAP_TIMEOUT = (10, 20). A slow upstream could therefore hold the response
for up to 60 seconds -- exactly the mobile client's receive timeout, which
reported "Something went wrong" for a registration that had actually succeeded,
and which the caller could not retry because the email address was taken.

Run:  ENV=development PYTHONPATH=. python tests/test_signup_latency.py
"""
import os
import sys
import threading
import time
import uuid
from datetime import date

from sqlalchemy import types as _satypes

_orig_bind = _satypes.Uuid.bind_processor


def _tolerant_bind(self, dialect):
    proc = _orig_bind(self, dialect)
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


_satypes.Uuid.bind_processor = _tolerant_bind

from flask import Flask  # noqa: E402

import src.resources  # noqa: F401,E402  (load order: resources before middlewares)
from src.models import CurrencyModel, UserModel, db  # noqa: E402
from src.resources import user as user_resource  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(_ROOT, 'templates'))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

SLOW = 3.0          # seconds each "Mailtrap" call blocks
_sends = []
_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<50} got={got!r} want={want!r}")


def slow_mailtrap(*args, **kwargs):
    time.sleep(SLOW)
    _sends.append(args[4] if len(args) > 4 else '?')   # subject
    return {'code': 200}


def register(**overrides):
    body = dict(first_name='New', last_name='User',
                email_address='slow@example.com', username='slowuser',
                mobile_number='8123456789', password='Abcdef1!x',
                gender='male', date_of_birth='1990-01-01')
    body.update(overrides)
    with app.test_request_context(json=body):
        response = user_resource.UserResource.create()
        return response[1] if isinstance(response, tuple) else 200


def main():
    user_resource.MailtrapHelper.mailtrap_email_sender = staticmethod(slow_mailtrap)

    with app.app_context():
        db.create_all()
        db.session.add(CurrencyModel(name='naira', short_code='ngn',
                                     country='nigeria'))
        db.session.commit()

        before = threading.active_count()
        started = time.monotonic()
        code = register()
        elapsed = time.monotonic() - started

        check('signup succeeds', code, 201)
        # Two 3s sends inline would be >= 6s. Off the request path it returns
        # immediately; allow generous headroom for a slow machine.
        print(f"       (responded in {elapsed:.2f}s; inline would be >= {2*SLOW:.0f}s)")
        check('  responds without waiting on the mail provider',
              elapsed < SLOW, True)
        check('  the account was committed',
              UserModel.query.filter_by(
                  email_address='slow@example.com').first() is not None, True)
        check('  background threads were started',
              threading.active_count() > before, True)

        # The sends must still actually happen.
        deadline = time.monotonic() + (2 * SLOW) + 10
        while len(_sends) < 2 and time.monotonic() < deadline:
            time.sleep(0.1)
        check('  both emails are sent, just later', len(_sends), 2)

        # A mail provider that throws must not affect the response.
        def exploding(*a, **k):
            raise RuntimeError('mailtrap is down')

        user_resource.MailtrapHelper.mailtrap_email_sender = staticmethod(exploding)
        code = register(email_address='boom@example.com', username='boomuser',
                        mobile_number='8123456700')
        check('a failing mail provider still returns created', code, 201)
        check('  and the account is committed',
              UserModel.query.filter_by(
                  email_address='boom@example.com').first() is not None, True)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
