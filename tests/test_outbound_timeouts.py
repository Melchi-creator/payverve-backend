"""Every outbound HTTP call must be bounded.

requests defaults to no timeout at all: a connection that is accepted and then
never answered blocks the worker indefinitely. Registration makes up to four
Flutterwave calls in series and sends the verification email inline, none of
which passed a timeout, so one stalled upstream took the whole signup past the
mobile client's 60s receive timeout. The client reported
"ERROR RESPONSE: null ... took longer than 0:01:00 to receive data" -- no status
code, because no response ever came.

BellbankHelper was already given this treatment and test_bellbank_client guards
it. This covers the two helpers that were missed.

Run:  ENV=development PYTHONPATH=. python tests/test_outbound_timeouts.py
"""
import sys

import requests

import src.resources  # noqa: F401  (import order: resources before middlewares)
from src.middlewares.flutterwave_helper import (FLUTTERWAVE_TIMEOUT,  # noqa: E402
                                                FlutterwaveHelper)
from src.middlewares.mailtrap_helper import (MAILTRAP_TIMEOUT,  # noqa: E402
                                             MailtrapHelper)

_failures = []
_seen = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<50} got={got!r} want={want!r}")


class FakeResponse:
    status_code = 200
    text = '{}'

    @staticmethod
    def json():
        return {'access_token': 'tok', 'data': {}}


def record(method, url, **kwargs):
    _seen.append({'method': method, 'url': url,
                  'timeout': kwargs.get('timeout')})
    return FakeResponse()


def boom(method, url, **kwargs):
    raise requests.exceptions.ReadTimeout('upstream stalled')


def main():
    requests.request = record

    # Each Flutterwave call registration depends on, in the order signup makes
    # them.
    _seen.clear()
    FlutterwaveHelper.flutterwave_authentication()
    FlutterwaveHelper.create_flutterwave_account(
        'tok', 'a@example.com', '8012345678', 'Ada', 'Obi')
    FlutterwaveHelper.search_for_customer('tok', 'a@example.com')
    FlutterwaveHelper.flutterwave_list_of_banks('NG')

    check('flutterwave: every call was recorded', len(_seen) >= 4, True)
    check('  and every one passes a timeout',
          all(c['timeout'] == FLUTTERWAVE_TIMEOUT for c in _seen), True)
    check('  with a bounded read deadline',
          FLUTTERWAVE_TIMEOUT[1] <= 30, True)

    _seen.clear()
    MailtrapHelper.mailtrap_email_sender(
        'PayVerve', 'no-reply@example.com', 'send',
        [{'email': 'a@example.com'}], 'Verify your email', '<p>code</p>')
    check('mailtrap: send passes a timeout',
          all(c['timeout'] == MAILTRAP_TIMEOUT for c in _seen), True)

    # The whole point of the deadline is that it surfaces as a clean failure
    # rather than a hang. Auth must report "unavailable", not hand its caller
    # something that gets interpolated into an Authorization header.
    requests.request = boom
    token = FlutterwaveHelper.flutterwave_authentication()
    check('a stalled auth returns None, not a jsonify tuple', token, None)
    check('  so it never becomes a Bearer header',
          isinstance(token, tuple), False)

    print()
    if _failures:
        print(f'{len(_failures)} FAILED: ' + ', '.join(_failures))
        return 1
    print('ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
