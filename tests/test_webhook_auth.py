"""The collection webhook must accept BellBank and refuse everyone else.

The route carries no jwt_required -- BellBank has no Payverve JWT, which is why
every notification used to come back 401. BellBank's public documentation
describes no webhook signature at all, so verification falls back to an IP
allowlist, and must still fail closed when neither is configured.

Run:  ENV=development PYTHONPATH=. python tests/test_webhook_auth.py
"""
import contextlib
import hashlib
import hmac
import io as _io
import json
import sys

from flask import Flask

import config
import src.resources  # noqa: F401  (import order: resources before middlewares)
from src.middlewares import BellbankHelper

app = Flask(__name__)
BODY = json.dumps({'event': 'collection', 'sessionId': 'S1',
                   'virtualAccount': '9901234567',
                   'amountReceived': 5000}).encode()
SECRET = 'a' * 64
BELL_IP = '102.89.10.20'

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


def sign(body, secret=SECRET):
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify(body=BODY, headers=None, secret=None, ips=''):
    config.bellbank_webhook_secret = secret
    config.bellbank_webhook_ips = ips
    config.bellbank_webhook_signature_header = 'X-Signature'
    with app.test_request_context(data=body, headers=headers or {}):
        return BellbankHelper.verify_bellbank_request(body)


def main():
    # Nothing configured -> fail closed.
    check('no secret and no ip allowlist rejected', verify(), False)

    # ...but it must say where the request came from, because BellBank does not
    # publish their addresses and the portal has no allowlist page. That log
    # line is the only way to learn what belongs in BELLBANK_WEBHOOK_IPS.
    log = _io.StringIO()
    with contextlib.redirect_stdout(log):
        verify(headers={'X-Forwarded-For': BELL_IP})
    output = log.getvalue()
    check('  and reports the source address for bootstrapping',
          BELL_IP in output, True)
    check('  and does not admit the request anyway',
          verify(headers={'X-Forwarded-For': BELL_IP}), False)

    # Signature path.
    check('valid signature accepted',
          verify(headers={'X-Signature': sign(BODY)}, secret=SECRET), True)
    check('  whitespace around signature tolerated',
          verify(headers={'X-Signature': f'  {sign(BODY)}  '}, secret=SECRET), True)
    check('forged signature rejected',
          verify(headers={'X-Signature': 'de' * 32}, secret=SECRET), False)
    check('tampered body rejected',
          verify(body=BODY.replace(b'5000', b'9999999'),
                 headers={'X-Signature': sign(BODY)}, secret=SECRET), False)

    # A bad signature must never fall through to the IP check.
    check('bad signature not rescued by an allowed ip',
          verify(headers={'X-Signature': 'de' * 32,
                          'X-Forwarded-For': BELL_IP},
                 secret=SECRET, ips=BELL_IP), False)

    # IP path, used when signing is not configured.
    check('allowed ip accepted when no secret set',
          verify(headers={'X-Forwarded-For': BELL_IP}, ips=BELL_IP), True)
    check('  one of several allowed ips accepted',
          verify(headers={'X-Forwarded-For': BELL_IP},
                 ips=f'1.2.3.4, {BELL_IP} ,5.6.7.8'), True)
    check('unknown ip rejected',
          verify(headers={'X-Forwarded-For': '203.0.113.9'}, ips=BELL_IP), False)
    check('proxy chain uses the client, not the proxy',
          verify(headers={'X-Forwarded-For': f'{BELL_IP}, 10.0.0.1, 10.0.0.2'},
                 ips=BELL_IP), True)

    # Secret set but BellBank sends no signature -> fall back, do not reject.
    check('no signature header falls back to ip',
          verify(headers={'X-Forwarded-For': BELL_IP},
                 secret=SECRET, ips=BELL_IP), True)
    check('  and still rejects an unknown ip',
          verify(headers={'X-Forwarded-For': '203.0.113.9'},
                 secret=SECRET, ips=BELL_IP), False)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
