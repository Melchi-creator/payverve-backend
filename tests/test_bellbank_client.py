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


def record(method, url, headers=None, json=None, timeout=None, proxies=None,
           **kw):
    _seen.append({'method': method, 'url': url, 'headers': headers or {},
                  'json': json, 'timeout': timeout, 'proxies': proxies})
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

    # Creating a client sends the fields BellBank's docs ask for. Without
    # emailAddress BellBank answered 500 instead of issuing an account.
    from datetime import date
    _seen.clear()
    BellbankHelper.bellbank_virtual_account(
        access_token='tok', mobile_number='08012345678', first_name='Ada',
        last_name='Obi', address='12 Broad St', bvn='22222222222',
        gender='Female', date_of_birth=date(1990, 1, 31),
        email_address='ada@example.com')
    body = _seen[0]['json']
    check('client creation sends emailAddress',
          body.get('emailAddress'), 'ada@example.com')
    check('  gender is lowercase male/female', body.get('gender'), 'female')
    check('  dateOfBirth is YYYY/MM/DD', body.get('dateOfBirth'), '1990/01/31')
    check('  posts to the individual client endpoint',
          _seen[0]['url'].endswith('/v1/account/clients/individual'), True)

    _seen.clear()
    BellbankHelper.bellbank_virtual_account(
        access_token='tok', mobile_number='08012345678', first_name='Ada',
        last_name='Obi', address='12 Broad St', bvn='22222222222',
        gender='male', date_of_birth='1990-01-31',
        email_address='ada@example.com')
    check('  a string date is reformatted too',
          _seen[0]['json'].get('dateOfBirth'), '1990/01/31')

    # Finding a client BellBank already created: BVN and email must both
    # match, so a shared BVN can never attach someone else's account.
    class _Clients:
        status_code = 200

        def __init__(self, data):
            self._data = data

        def json(self):
            return {'success': True, 'data': self._data}

    clients = [
        {'bvn': '22222222222', 'emailAddress': 'someone@else.com',
         'accountNumber': '1111111111'},
        {'bvn': '22222222222', 'emailAddress': 'Ada@Example.com',
         'accountNumber': '1000137010', 'externalReference': 'ref-1'},
    ]
    _seen.clear()
    helper.requests.request = lambda m, u, **k: (
        _seen.append({'url': u, 'proxies': k.get('proxies')})
        or _Clients(clients))
    found = BellbankHelper.find_individual_client(
        'tok', '22222222222', 'ada@example.com')
    check('client lookup matches bvn and email',
          found and found['accountNumber'], '1000137010')
    check('  queries individual clients',
          '/v1/account/clients?accountType=individual' in _seen[0]['url'],
          True)
    check('  a matching bvn with another email is not a match',
          BellbankHelper.find_individual_client(
              'tok', '22222222222', 'nobody@example.com'), None)
    check('  no bvn means no lookup',
          BellbankHelper.find_individual_client('tok', '', 'ada@example.com'),
          None)
    helper.requests.request = lambda m, u, **k: _Clients(
        {'data': clients, 'total': 2})
    check('  a list nested under data.data is read too',
          (BellbankHelper.find_individual_client(
              'tok', '22222222222', 'ada@example.com') or {})
          .get('accountNumber'), '1000137010')
    masked = [{'bvn': '222****2222', 'emailAddress': 'ada@example.com',
               'accountNumber': '1000137010'}]
    helper.requests.request = lambda m, u, **k: _Clients(masked)
    check('  a masked bvn still matches on email',
          (BellbankHelper.find_individual_client(
              'tok', '22222222222', 'ada@example.com') or {})
          .get('accountNumber'), '1000137010')
    other = [{'bvn': '99999999999', 'emailAddress': 'ada@example.com',
              'accountNumber': '1000137010'}]
    helper.requests.request = lambda m, u, **k: _Clients(other)
    check('  same email with a different bvn is refused',
          BellbankHelper.find_individual_client(
              'tok', '22222222222', 'ada@example.com'), None)
    helper.requests.request = lambda m, u, **k: _Clients({'oops': 1})
    check('  an unexpected response is no match',
          BellbankHelper.find_individual_client(
              'tok', '22222222222', 'ada@example.com'), None)
    helper.requests.request = record

    # With no proxy configured, calls go straight to BellBank.
    original_proxy = getattr(config, 'bellbank_proxy_url', '')
    config.bellbank_proxy_url = ''
    _seen.clear()
    transfer('REF-PRX')
    check('no proxy configured: calls go direct',
          _seen[0]['proxies'], None)

    # With one configured, every call leaves through it -- that is what
    # BellBank's IP whitelist sees.
    proxy = 'http://user:secret@proxy.example:80'
    config.bellbank_proxy_url = proxy
    _seen.clear()
    BellbankHelper.bellbank_authentication('5')
    transfer('REF-PRX')
    BellbankHelper.transfer_requery('REF-PRX', 'tok')
    BellbankHelper.list_bell_ngn_banks()
    check('proxy configured: every call uses it for https',
          all(c['proxies'] == {'http': proxy, 'https': proxy} for c in _seen),
          True)
    check('  and token generation is one of them',
          'generate-token' in _seen[0]['url'], True)

    config.bellbank_proxy_url = '  '
    _seen.clear()
    transfer('REF-PRX')
    check('a blank proxy setting means direct',
          _seen[0]['proxies'], None)
    config.bellbank_proxy_url = original_proxy

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
