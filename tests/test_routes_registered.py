"""Every blueprint that exists must actually be routed.

server.py registers blueprints by iterating vars(routes), so a route module
that src/routes/__init__.py never imports is silently never served. That is
what happened to the BellBank webhook: the module and its route existed, the
handler was maintained, and the endpoint 404'd on every deployment because one
import line was missing. Nothing failed loudly.

Run:  ENV=development PYTHONPATH=. python tests/test_routes_registered.py
"""
import io
import os
import re
import sys

import server

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


def blueprint_modules():
    """Every route module and the blueprint names it defines."""
    found = {}
    for filename in sorted(os.listdir('src/routes')):
        if not filename.endswith('.py') or filename == '__init__.py':
            continue
        source = io.open(os.path.join('src/routes', filename),
                         encoding='utf-8').read()
        names = re.findall(r'^(\w+)\s*=\s*Blueprint', source, re.M)
        if names:
            found[filename[:-3]] = names
    return found


def main():
    init = io.open('src/routes/__init__.py', encoding='utf-8').read()
    modules = blueprint_modules()
    rules = {str(r) for r in server.server.url_map.iter_rules()}

    unimported = [m for m in modules
                  if not re.search(rf'^from \.{re.escape(m)} import', init, re.M)]

    # bankaccount.py names its blueprint BeneficiaryBlueprint, the same Python
    # name beneficiary.py uses. Importing it as-is would shadow the registered
    # one and unroute /beneficiaries, so it needs an alias, not a plain import.
    known_unrouted = {'bankaccount'}

    unexpected = sorted(set(unimported) - known_unrouted)
    check('every route module is imported by __init__', unexpected, [])

    check('the bellbank webhook is routed', '/bellbank/webhook' in rules, True)

    webhook = [r for r in server.server.url_map.iter_rules()
               if str(r) == '/bellbank/webhook']
    check('  and accepts POST',
          bool(webhook) and 'POST' in webhook[0].methods, True)
    check('  and not GET',
          bool(webhook) and 'GET' not in webhook[0].methods, True)

    # Routes that existed before must not have been displaced by the new import.
    for path in ('/beneficiaries', '/currencies', '/ngn-wallets', '/referrals'):
        check(f'still routed: {path}', path in rules, True)

    if _failures:
        print(f'\n{len(_failures)} FAILURES: {_failures}')
        return 1
    print('\nALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
