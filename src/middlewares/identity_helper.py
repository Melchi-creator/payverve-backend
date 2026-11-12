"""Check a customer's claimed identity against the BVN record before it is used.

Nothing verified these fields. Registration stored whatever was typed -- the
only check was that the date of birth implied eighteen or over -- and KYC passed
the result straight to BellBank, which creates the client and runs the BVN
check itself. A mismatch therefore surfaced as "Recipient's KYC verification
incomplete" on a failed inbound transfer, long after the client existed, and
BellBank offers no way to correct one: the client has to be deleted and
recreated. One real account reached that state with three wrong fields at once
(gender, date of birth, and a NIN that was never sent at all).

Catching it at the KYC step costs one lookup and turns an unrecoverable
provisioning failure into a form error the customer can act on.

WHAT THIS DELIBERATELY DOES NOT DO
----------------------------------
It never returns the values held against the BVN, only which of the submitted
fields disagree. Echoing them back would turn KYC into a lookup service: submit
any BVN, read the owner's name and date of birth out of the error message.

CONFIGURATION
-------------
Set DOJAH_APP_ID and DOJAH_SECRET_KEY to enable it. With neither set, lookups
are skipped and KYC behaves exactly as it did before -- the pre-existing
behaviour, not a new hole -- and every skip is logged. Configure it before
onboarding real customers: until then any customer can self-report an identity
that does not match their BVN and end up with an account nobody can pay.

The endpoint and response shape follow Dojah's BVN lookup. Field names are read
defensively because providers differ on camelCase versus snake_case, and the
adapter is small enough to swap for another provider.
"""
import re
from datetime import date, datetime

import requests

import config

# (connect, read). An identity provider is in the middle of a customer-facing
# form, so it must not be able to hang the request.
IDENTITY_TIMEOUT = (10, 20)

_DATE_FORMATS = ('%Y-%m-%d', '%d-%m-%Y', '%Y/%m/%d', '%d/%m/%Y',
                 '%d-%b-%Y', '%d %B %Y', '%Y-%m-%dT%H:%M:%S',
                 '%Y-%m-%dT%H:%M:%S.%fZ')


class BvnCheck:
    """The outcome of a BVN lookup.

    `checked` says whether a provider actually answered. False means no
    verification happened -- not configured, unreachable, or the BVN was not
    found -- and the caller must decide what to do, rather than reading
    `ok` as a pass.
    """

    def __init__(self, checked, ok=True, mismatches=None, reason=None):
        self.checked = checked
        self.ok = ok
        self.mismatches = mismatches or []
        self.reason = reason

    def __repr__(self):
        return (f'BvnCheck(checked={self.checked}, ok={self.ok}, '
                f'mismatches={self.mismatches})')


def is_configured():
    """Whether an identity provider is available to call."""
    return bool((getattr(config, 'dojah_app_id', '') or '').strip()
                and (getattr(config, 'dojah_secret_key', '') or '').strip())


def _normalise_name(value):
    """Casefold and strip anything that is not a letter.

    Names come back from the provider punctuated and spaced differently from
    how they were typed -- "O'Brien" against "OBrien", double spaces, hyphens.
    """
    return re.sub(r'[^a-z]', '', str(value or '').lower())


def _parse_date(value):
    """A date from whatever shape the provider returned, or None."""
    if value in (None, ''):
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _first_present(record, *names):
    """The first of `names` present in the record, camelCase or snake_case."""
    for name in names:
        for key in (name, name.lower(),
                    re.sub(r'_([a-z])', lambda m: m.group(1).upper(), name)):
            if key in record and record[key] not in (None, ''):
                return record[key]
    return None


def lookup_bvn(bvn):
    """The identity the provider holds against this BVN, or None.

    Returns a dict with first_name, last_name, middle_name, date_of_birth and
    gender, normalised. Never raises: a provider outage must not take the KYC
    endpoint down with it.
    """
    if not is_configured():
        return None

    try:
        base = (getattr(config, 'dojah_base_url', '')
                or 'https://api.dojah.io').rstrip('/')
        url = f'{base}/api/v1/kyc/bvn/full'

        response = requests.get(
            url,
            params={'bvn': str(bvn).strip()},
            headers={
                'AppId': config.dojah_app_id,
                'Authorization': config.dojah_secret_key,
                'accept': 'application/json',
            },
            timeout=IDENTITY_TIMEOUT)

        if response.status_code != 200:
            # Deliberately does not log the bvn.
            print(f'[identity] bvn lookup returned HTTP '
                  f'{response.status_code}')
            return None

        body = response.json() or {}
        entity = body.get('entity') or body.get('data') or body

        if not isinstance(entity, dict) or not entity:
            print('[identity] bvn lookup returned no entity')
            return None

        return {
            'first_name': _first_present(entity, 'first_name', 'firstName'),
            'last_name': _first_present(entity, 'last_name', 'lastName',
                                        'surname'),
            'middle_name': _first_present(entity, 'middle_name', 'middleName'),
            'date_of_birth': _parse_date(
                _first_present(entity, 'date_of_birth', 'dateOfBirth', 'dob')),
            'gender': str(_first_present(entity, 'gender') or '').strip().lower(),
        }

    except Exception as e:
        print(f'[identity] bvn lookup failed: {type(e).__name__}: {e}')
        return None


def verify_bvn_identity(bvn, first_name=None, last_name=None,
                        date_of_birth=None, gender=None):
    """Compare submitted details against the BVN record.

    Returns a BvnCheck. mismatches names the submitted fields that disagree and
    nothing else -- see the module docstring on why the real values stay here.
    """
    if not is_configured():
        print('[identity] BVN verification is not configured '
              '(DOJAH_APP_ID / DOJAH_SECRET_KEY); identity was NOT checked')
        return BvnCheck(checked=False, reason='not configured')

    record = lookup_bvn(bvn)

    if record is None:
        return BvnCheck(checked=False, reason='lookup unavailable')

    mismatches = []

    # Names: the record's first name sometimes carries the middle name too, so
    # compare against the whole of the record's names rather than field to
    # field, and only complain when a submitted name appears nowhere in it.
    record_names = {_normalise_name(record.get(k))
                    for k in ('first_name', 'last_name', 'middle_name')}
    record_names.discard('')

    for label, submitted in (('first_name', first_name),
                             ('last_name', last_name)):
        wanted = _normalise_name(submitted)

        if not wanted:
            continue

        if not any(wanted == held or wanted in held or held in wanted
                   for held in record_names):
            mismatches.append(label)

    held_dob = record.get('date_of_birth')
    given_dob = _parse_date(date_of_birth)

    if held_dob and given_dob and held_dob != given_dob:
        mismatches.append('date_of_birth')

    held_gender = (record.get('gender') or '').strip().lower()
    given_gender = str(gender or '').strip().lower()

    # Compare on the first letter: providers return 'M', 'Male' and 'male'.
    if held_gender and given_gender and held_gender[0] != given_gender[0]:
        mismatches.append('gender')

    return BvnCheck(checked=True, ok=not mismatches, mismatches=mismatches)
