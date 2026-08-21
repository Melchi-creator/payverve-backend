"""Deposit and withdrawal must reach the device, not just the database.

Every money-movement path called NotificationResource.store_nofication, which
writes a row and nothing else. send_push_notification was wired into exactly
one place -- the Flutterwave webhook -- so BellBank deposits produced no push
at all, and withdrawals produced none on either rail. The in-app notification
list filled up correctly, which is what made it easy to miss.

store_and_push does both halves, and must never let a push failure propagate
back into the transaction that triggered it: by then the money has moved.

Run:  ENV=development PYTHONPATH=. python tests/test_push_notifications.py
"""
import sys
import uuid
from datetime import date

# The resources pass UUIDs straight through as strings. Postgres accepts that;
# SQLite's Uuid bind processor demands a uuid.UUID. Shim it so these tests
# exercise the real code path rather than a dialect quirk.
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

from flask import Flask  # noqa: E402

from src.models import NotificationModel, UserModel, db  # noqa: E402
from src.resources import notification as notification_module  # noqa: E402
from src.resources.notification import NotificationResource  # noqa: E402

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

_failures = []
_sent = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


def fake_send(fcm_token, title, body, data=None):
    _sent.append({'token': fcm_token, 'title': title,
                  'body': body, 'data': data})
    return True


def exploding_send(fcm_token, title, body, data=None):
    raise RuntimeError('firebase is down')


def make_user(name, token):
    user = UserModel(first_name=name, last_name='Test',
                     email_address=f'{name}@example.com', username=name,
                     mobile_number=f'8000{abs(hash(name)) % 100000:05d}',
                     user_code=name.upper(), gender='male',
                     date_of_birth=date(1990, 1, 1))
    user.set_password('Abcdef1!x')
    user.fcm_token = token
    db.session.add(user)
    db.session.commit()
    return user


def main():
    with app.app_context():
        db.create_all()
        notification_module.send_push_notification = fake_send

        with_token = make_user('deposited', 'fcm-token-abc')
        without_token = make_user('tokenless', None)

        # A deposit stores the row AND pushes it.
        _sent.clear()
        NotificationResource.store_and_push(
            title='Wallet Funded', body='NGN 5,000.00 received',
            user_id=with_token.id,
            data={'type': 'wallet_credit', 'amount': 5000.0})

        check('deposit sends exactly one push', len(_sent), 1)
        check('  to the right device', _sent[0]['token'], 'fcm-token-abc')
        check('  carrying the alert title', _sent[0]['title'], 'Wallet Funded')
        check('  and the in-app row is still written',
              NotificationModel.query.filter_by(
                  user_id=with_token.id).count(), 1)

        # FCM rejects a data payload whose values are not all strings, so the
        # float amount has to be stringified before it reaches the SDK.
        check('  numeric data is stringified for FCM',
              _sent[0]['data'], {'type': 'wallet_credit', 'amount': '5000.0'})

        # A withdrawal is the same contract with the opposite flow.
        _sent.clear()
        NotificationResource.store_and_push(
            title='Local Transfer', body='NGN 2,000.00 sent to Jane',
            user_id=with_token.id,
            data={'type': 'wallet_debit', 'amount': 2000.0})
        check('withdrawal pushes too', len(_sent), 1)
        check('  flagged as a debit',
              _sent[0]['data']['type'], 'wallet_debit')

        # A user who never registered a device still gets the in-app row.
        _sent.clear()
        NotificationResource.store_and_push(
            title='Wallet Funded', body='NGN 100.00 received',
            user_id=without_token.id, data={'type': 'wallet_credit'})
        check('no token means no push attempt', len(_sent), 0)
        check('  but the row is still stored',
              NotificationModel.query.filter_by(
                  user_id=without_token.id).count(), 1)

        # The money already moved; Firebase falling over cannot undo it.
        notification_module.send_push_notification = exploding_send
        raised = False
        try:
            NotificationResource.store_and_push(
                title='Wallet Funded', body='NGN 250.00 received',
                user_id=with_token.id, data={'type': 'wallet_credit'})
        except Exception:
            raised = True
        check('a firebase outage never propagates', raised, False)
        check('  and the row survives it',
              NotificationModel.query.filter_by(
                  user_id=with_token.id).count(), 3)

    print()
    if _failures:
        print(f'{len(_failures)} FAILED: ' + ', '.join(_failures))
        return 1
    print('ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
