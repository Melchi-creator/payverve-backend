"""A customer's details must agree with their BVN before KYC accepts them.

Nothing checked these. Registration stored whatever was typed -- the only
validation was that the date of birth implied eighteen or over -- and KYC
handed the result to BellBank, which runs the BVN check itself when it creates
the client. A mismatch therefore appeared as "Recipient's KYC verification
incomplete" on a failed inbound transfer, after the client already existed, and
BellBank cannot correct one: the client has to be deleted and recreated.

One real account reached that state with gender wrong, a date of birth sixteen
years out, and a NIN that was never sent at all.

Run:  ENV=development PYTHONPATH=. python tests/test_bvn_identity_check.py
"""
import sys
from datetime import date

import src.resources  # noqa: F401  (import order: resources before middlewares)
from src.middlewares import identity_helper as ih

_failures = []


def check(label, got, want):
    ok = got == want
    if not ok:
        _failures.append(label)
    print(f"{'PASS' if ok else 'FAIL'}  {label:<52} got={got!r} want={want!r}")


# What the provider holds against the BVN under test.
HELD = {
    'first_name': 'OGONNAYA',
    'last_name': 'AJA',
    'middle_name': 'EDWARD',
    'date_of_birth': date(1984, 4, 4),
    'gender': 'male',
}


def main():
    ih.is_configured = lambda: True
    ih.lookup_bvn = lambda bvn: dict(HELD)

    # The details that actually matched.
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya',
                               last_name='Aja', date_of_birth=date(1984, 4, 4),
                               gender='male')
    check('matching details pass', (r.checked, r.ok), (True, True))

    # The three that were wrong on the real account.
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya',
                               last_name='Aja', date_of_birth=date(2000, 1, 20),
                               gender='female')
    check('the real mismatch is caught', r.ok, False)
    check('  and names both wrong fields',
          sorted(r.mismatches), ['date_of_birth', 'gender'])

    # Formatting differences are not mismatches.
    r = ih.verify_bvn_identity('22222222222', first_name='  ogonnaya ',
                               last_name="A'ja", date_of_birth='1984-04-04',
                               gender='Male')
    check('case, spacing and punctuation are tolerated', r.ok, True)
    check('  as are provider date strings and M/Male',
          r.mismatches, [])

    # A record whose first name carries the middle name too.
    ih.lookup_bvn = lambda bvn: dict(HELD, first_name='OGONNAYA EDWARD')
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya',
                               last_name='Aja', date_of_birth=date(1984, 4, 4),
                               gender='male')
    check('a combined first/middle name still matches', r.ok, True)
    ih.lookup_bvn = lambda bvn: dict(HELD)

    # A wrong surname is caught.
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya',
                               last_name='Okafor', date_of_birth=date(1984, 4, 4),
                               gender='male')
    check('a wrong surname is caught', r.mismatches, ['last_name'])

    # Unavailable is not a pass. `checked` is what the caller must read.
    ih.lookup_bvn = lambda bvn: None
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya',
                               last_name='Aja')
    check('a failed lookup reports checked=False', r.checked, False)
    check('  so KYC does not treat it as verified', (r.checked and r.ok), False)

    ih.is_configured = lambda: False
    r = ih.verify_bvn_identity('22222222222', first_name='Ogonnaya')
    check('unconfigured reports checked=False', r.checked, False)

    # The endpoint must not become a BVN lookup service: a mismatch may say
    # which fields disagree and never what the record holds.
    ih.is_configured = lambda: True
    ih.lookup_bvn = lambda bvn: dict(HELD)
    r = ih.verify_bvn_identity('22222222222', first_name='Wrong',
                               last_name='Person', date_of_birth=date(1999, 9, 9),
                               gender='female')
    leaked = [v for v in ('OGONNAYA', 'AJA', 'EDWARD', '1984', 'male')
              if any(v.lower() in str(m).lower() for m in r.mismatches)]
    check('mismatches name fields only, never held values', leaked, [])
    check('  and all four are reported', len(r.mismatches), 4)

    print()
    if _failures:
        print(f'{len(_failures)} FAILED: ' + ', '.join(_failures))
        return 1
    print('ALL PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())
