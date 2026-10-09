"""Delete test users and everything that belongs to them.

A user is referenced from many tables (wallets, kycs, virtual_account_numbers,
transactions, transfers, notifications, ...), and some of those are referenced
in turn (transfers point at wallets). Rather than keep a hand-written list that
drifts from the real schema, this reads the foreign keys from the database it
is connected to and deletes children before parents. It also removes the
user's referral rows and pending verification codes, which point at a user by
value rather than by foreign key.

It does NOT touch BellBank. A client created there keeps its email, BVN and
account number, so re-registering with the same email will be refused by
BellBank ('Email address already exists') and Payverve will re-attach the old
account. Ask BellBank to remove the client, or register with a new email.

DRY RUN BY DEFAULT: it prints what it would delete and rolls back. Pass
--apply to delete. Everything happens in one transaction, so a failure part
way leaves the database untouched.

    python scripts/delete_users.py --mobile 8063770187 --mobile 9034837062
    python scripts/delete_users.py --mobile 8063770187 --mobile 9034837062 --apply
"""
import argparse
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa  # noqa: E402

import config  # noqa: E402


def foreign_key_children(inspector):
    """{parent_table: [(child_table, child_column, parent_column)]}"""
    children = defaultdict(list)

    for table in inspector.get_table_names():
        for fk in inspector.get_foreign_keys(table):
            if len(fk['constrained_columns']) != 1:
                continue
            children[fk['referred_table']].append(
                (table, fk['constrained_columns'][0], fk['referred_columns'][0]))

    return children


def collect(conn, children, table, column, values, plan, seen):
    """Add every row reachable from table.column IN values to plan, children
    first, so deleting in plan order never breaks a foreign key."""
    if not values:
        return

    rows = conn.execute(
        sa.text(f'SELECT * FROM "{table}" WHERE "{column}"::text = ANY(:v)'),
        {'v': list(values)}).mappings().all()

    if not rows:
        return

    for child_table, child_column, parent_column in children.get(table, []):
        parent_values = {str(r[parent_column]) for r in rows
                         if r.get(parent_column) is not None}
        collect(conn, children, child_table, child_column, parent_values,
                plan, seen)

    key = (table, column)
    plan.setdefault(key, set()).update(str(v) for v in values)
    seen[table] = seen.get(table, 0) + len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mobile', action='append', default=[],
                        help='mobile_number as stored, e.g. 9034837062')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    if not args.mobile:
        parser.error('give at least one --mobile')

    url = config.database_uri
    host = sa.engine.make_url(url).host
    print(f'database host: {host}')
    print('MODE: ' + ('APPLY - rows will be deleted' if args.apply
                      else 'dry run - nothing will be deleted'))

    engine = sa.create_engine(url)

    with engine.connect() as conn:
        trans = conn.begin()

        users = conn.execute(sa.text(
            'SELECT id, first_name, last_name, email_address, mobile_number '
            'FROM users WHERE mobile_number = ANY(:m)'),
            {'m': args.mobile}).mappings().all()

        missing = set(args.mobile) - {u['mobile_number'] for u in users}
        if missing:
            print(f'no user with mobile number(s): {sorted(missing)}')

        if not users:
            trans.rollback()
            return 1

        for u in users:
            print(f"user {u['id']}  {u['first_name']} {u['last_name']}  "
                  f"{u['email_address']}  {u['mobile_number']}")

        user_ids = {str(u['id']) for u in users}
        contacts = ({u['email_address'] for u in users}
                    | {u['mobile_number'] for u in users})

        inspector = sa.inspect(conn)
        children = foreign_key_children(inspector)
        plan, counts = {}, {}
        collect(conn, children, 'users', 'id', user_ids, plan, counts)

        # Linked by value, not by foreign key.
        tables = set(inspector.get_table_names())
        extra = []
        if 'referrals' in tables:
            extra.append(('referrals',
                          'referral_id::text = ANY(:ids) OR referred_id::text = ANY(:ids)',
                          {'ids': list(user_ids)}))
        if 'token_verifications' in tables:
            extra.append(('token_verifications',
                          'channel_contact::text = ANY(:c)',
                          {'c': list(contacts)}))

        print('\nrows to delete:')
        for table, where, params in extra:
            n = conn.execute(sa.text(
                f'SELECT COUNT(*) FROM "{table}" WHERE {where}'),
                params).scalar()
            print(f'  {table:<28} {n}')
        for table, n in counts.items():
            print(f'  {table:<28} {n}')

        for table, where, params in extra:
            conn.execute(sa.text(f'DELETE FROM "{table}" WHERE {where}'),
                         params)
        for (table, column), values in plan.items():
            conn.execute(
                sa.text(f'DELETE FROM "{table}" WHERE "{column}"::text = ANY(:v)'),
                {'v': list(values)})

        left = conn.execute(sa.text(
            'SELECT COUNT(*) FROM users WHERE id::text = ANY(:ids)'),
            {'ids': list(user_ids)}).scalar()

        if args.apply:
            trans.commit()
            print(f'\ndeleted. users remaining with those ids: {left}')
        else:
            trans.rollback()
            print(f'\ndry run: the deletes succeeded inside a transaction '
                  f'(users remaining: {left}) and were rolled back. '
                  f'Re-run with --apply to delete.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
