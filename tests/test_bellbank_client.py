"""The BellBank client must key transfers correctly and fail safely.

The idempotency key used to be built from sender, amount, bank code, account
number and recipient. Two genuine transfers of the same amount to the same
person therefore carried the same key: BellBank collapses the second into the
first, while the caller reads the 200 as success and debits the wallet again.

Run:  ENV=development PYTHONPATH=. python tests/test_bellbank_client.py
"""
import sys

import src.resources  # noqa: F401  (import order: resources before middlewares)
import config
from src.middlewares import BellbankHelper
from src.middlewares.bellbank_helper import BELLBANK_TIMEOUT, bellbank_url

_failures = []
_seen = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


class _Recorder:
    """Stands in for requests.request and records what was sent."""
    status_code = 200

    @staticmethod
    def json():
        return {'data': {}}


def record(method, url, headers=None, json=None, timeout=None, **kw):
    _seen.append({'method': method, 'url': url, 'headers': headers or {},
                  'json': json, 'timeout': timeout})
    return _Recorder()


def transfer(reference, amount='5000', recipient='Ada Obi'):
    return BellbankHelper.transfer_outbound(
        bank_code='044', amount=amount, narration='test',
        account_number='0123456789', reference=reference,
        sender_name='Chidi Eze', recipient_name=recipient,
        access_token='tok')


def main():
    import src.middlewares.bellbank_helper as helper
    helper.requests.request = record

    # Two identical-looking transfers with different references.
    transfer('REF-AAA')
    transfer('REF-BBB')
    first, second = _seen[0], _seen[1]

    check('two distinct transfers get distinct idempotency keys',
          first['headers']['X-Idempotency-Key']
          != second['headers']['X-Idempotency-Key'], True)

    # A retry of the SAME transfer must reuse its key.
    _seen.clear()
    transfer('REF-AAA')
    transfer('REF-AAA')
    check('a retry of one transfer reuses its key',
          _seen[0]['headers']['X-Idempotency-Key']
          == _seen[1]['headers']['X-Idempotency-Key'], True)

    # The key must not be the raw reference, and must not leak the secret.
    key = _seen[0]['headers']['X-Idempotency-Key']
    check('  key is a digest, not the raw reference', key != 'REF-AAA', True)
    check('  key is sha256 hex', len(key) == 64, True)
    check('  key does not contain the signing secret',
          config.secret_key not in key, True)

    # Every call must be bounded.
    _seen.clear()
    transfer('REF-CCC')
    BellbankHelper.transfer_requery('REF-CCC', 'tok')
    BellbankHelper.list_bell_ngn_banks()
    check('every call passes a timeout',
          all(c['timeout'] == BELLBANK_TIMEOUT for c in _seen), True)

    # Paths carry the version prefix.
    check('transfer url is versioned',
          bellbank_url('transfer').endswith('/v1/transfer'), True)

    # A network failure must be checkable, not a jsonify tuple.
    def boom(*a, **k):
        raise ConnectionError('bank unreachable')

    helper.requests.request = boom
    check('network failure returns None, not a tuple',
          transfer('REF-DDD'), None)
    check('  auth failure returns None too',
          BellbankHelper.bellbank_authentication('5'), None)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
