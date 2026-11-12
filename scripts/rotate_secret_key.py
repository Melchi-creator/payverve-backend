"""Recompute the stored hashes after SECRET_KEY is changed.

SECRET_KEY keys hash_identifier(), and two kinds of stored value depend on it:

  kycs.bvn_hash / kycs.nin_hash   the duplicate-BVN / duplicate-NIN check.
                                  Rebuilt here: the BVN and NIN themselves are
                                  stored encrypted under the Fernet keys,
                                  which are not changing, so each hash can be
                                  recomputed under the new key.

  merchants.secret_key_hash       CANNOT be rebuilt: the plaintext secret key
                                  is never stored. Every merchant key issued
                                  under the old SECRET_KEY stops working. This
                                  script lists the shops affected; each owner
                                  issues a new key with
                                  POST /merchants/me/secret-key.

Order of operations in production:

  1. Generate a new key (64 hex characters).
  2. Dry run, to see that every row will rebuild:
         $env:NEW_SECRET_KEY = "<new key>"
         python scripts/rotate_secret_key.py --prod
  3. Set SECRET_KEY to the new key on Render and let it restart.
  4. Straight away:
         python scripts/rotate_secret_key.py --prod --apply
     Between steps 3 and 4 the duplicate check compares new-key hashes with
     old-key hashes, so a customer re-using a BVN in that minute would not be
     caught. Keep the gap short.
  5. Put the new key in your local .env as well.

The old key is read from SECRET_KEY in .env (or OLD_SECRET_KEY if set) and
only used to confirm the stored hashes really were made with it, so a typo'd
or already-rotated key is reported rather than silently trusted.

DRY RUN BY DEFAULT. Everything is one transaction: a failure part way leaves
the database untouched.
"""
import argparse
import hashlib
import hmac
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _select_production_database():
    """Point this process at the non-local DATABASE_URL in .env.

    .env defines DATABASE_URL more than once and dotenv keeps the last, which
    is localhost. Same approach as delete_users.py: read it from the file so
    the password never touches the command line. Must run before config is
    imported, because config reads the url at import time.
    """
    import io as _io
    import re as _re

    env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')

    if not os.path.exists(env_path):
        raise SystemExit('no .env to read a production DATABASE_URL from')

    contents = _io.open(env_path, encoding='utf-8').read()
    candidates = [u.strip().strip('"').strip("'")
                  for u in _re.findall(r'^DATABASE_URL=(.+)$', contents, _re.M)]
    remote = [u for u in candidates
              if 'localhost' not in u and '127.0.0.1' not in u]

    if not remote:
        raise SystemExit('no non-local DATABASE_URL found in .env')

    # Not DATABASE_URL: config loads .env with override=True, which would
    # replace it with .env's localhost entry.
    os.environ['DATABASE_URL_OVERRIDE'] = remote[0]
    return _re.sub(r'://[^@]*@', '://***@', remote[0])


if '--prod' in sys.argv:
    sys.argv.remove('--prod')
    print(f'database: {_select_production_database()}')

import sqlalchemy as sa  # noqa: E402

import config  # noqa: E402
from src.utilities.sensitive_id import _clean, decrypt_identifier  # noqa: E402


def keyed_hash(key, value):
    """hash_identifier() under an explicit key."""
    text = _clean(value)
    if text is None:
        return None
    return hmac.new(key.encode(), text.encode(), hashlib.sha256).hexdigest()


def plan(conn, old_key, new_key):
    """What would change. Returns (updates, problems, merchants)."""
    rows = conn.execute(sa.text(
        'SELECT id, bvn, bvn_hash, nin, nin_hash FROM kycs')).mappings().all()

    updates, problems = [], []

    for row in rows:
        change = {'id': row['id']}

        for field in ('bvn', 'nin'):
            stored_hash = row[f'{field}_hash']
            plaintext = decrypt_identifier(row[field])

            if row[field] is None and stored_hash is None:
                continue

            if plaintext is None:
                problems.append(f'kyc {row["id"]}: {field} cannot be '
                                f'decrypted; its hash is left as it is')
                continue

            if stored_hash and keyed_hash(old_key, plaintext) != stored_hash:
                problems.append(f'kyc {row["id"]}: stored {field}_hash was not '
                                f'made with the old key; recomputed anyway')

            new_hash = keyed_hash(new_key, plaintext)
            if new_hash != stored_hash:
                change[f'{field}_hash'] = new_hash

        if len(change) > 1:
            updates.append(change)

    # A database not yet migrated to the merchant tables has no keys to lose.
    merchants = conn.execute(sa.text(
        'SELECT business_name, secret_key_preview FROM merchants '
        'WHERE is_active')).all() \
        if sa.inspect(conn).has_table('merchants') else []

    return len(rows), updates, problems, merchants


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    new_key = (os.getenv('NEW_SECRET_KEY') or '').strip()
    old_key = (os.getenv('OLD_SECRET_KEY') or config.secret_key or '').strip()

    if len(new_key) < 32:
        raise SystemExit('set NEW_SECRET_KEY to the new key (at least 32 '
                         'characters)')
    if not old_key:
        raise SystemExit('no old key: set SECRET_KEY in .env or OLD_SECRET_KEY')
    if new_key == old_key:
        raise SystemExit('NEW_SECRET_KEY is the same as the old key')

    url = config.database_uri
    connect_args = {} if ('localhost' in url or '127.0.0.1' in url) \
        else {'sslmode': 'require'}
    engine = sa.create_engine(url, connect_args=connect_args)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            total, updates, problems, merchants = plan(conn, old_key, new_key)

            # Clear first, then write: a new hash colliding with a not-yet
            # rewritten old hash would trip the unique constraint midway.
            for change in updates:
                for column in ('bvn_hash', 'nin_hash'):
                    if column in change:
                        conn.execute(sa.text(
                            f'UPDATE kycs SET {column} = NULL WHERE id = :id'),
                            {'id': change['id']})
            for change in updates:
                for column in ('bvn_hash', 'nin_hash'):
                    if column in change:
                        conn.execute(sa.text(
                            f'UPDATE kycs SET {column} = :h WHERE id = :id'),
                            {'h': change[column], 'id': change['id']})

            print(f'kyc rows: {total}; rows whose hashes change: '
                  f'{len(updates)}')
            for problem in problems:
                print(f'  ! {problem}')

            if merchants:
                print(f'\n{len(merchants)} active merchant(s) will need a new '
                      f'secret key (POST /merchants/me/secret-key):')
                for name, preview in merchants:
                    print(f'  - {name} (key ...{preview})')
            else:
                print('no active merchants; no API keys are affected')

            if args.apply:
                trans.commit()
                print('\nAPPLIED. Make sure SECRET_KEY on Render is the new key.')
            else:
                trans.rollback()
                print('\nDRY RUN, nothing written. Re-run with --apply.')
        except Exception:
            trans.rollback()
            raise


if __name__ == '__main__':
    main()
