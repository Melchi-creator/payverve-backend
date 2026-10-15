"""encrypt bvn and nin at rest, move uniqueness onto a keyed hash

kycs.bvn and kycs.nin held bare plaintext with unique=True, while wallet
balances -- far less sensitive -- were already encrypted. GET /kycs returned
them in full to any authenticated caller, so a single request read every
customer's BVN.

Uniqueness cannot stay on the value column once it is encrypted: Fernet is
non-deterministic, so the same BVN produces different ciphertext every time and
the constraint would no longer reject a duplicate. It moves to bvn_hash /
nin_hash, a keyed HMAC-SHA256 of the identifier -- stable for a given input,
and not reversible by anyone without the secret, unlike a bare digest over the
~10^11 possible BVNs.

The backfill is idempotent: it decrypts through utilities.decrypt_identifier,
which accepts both a legacy plaintext row and an already-encrypted one, so a
re-run re-encrypts from the same plaintext and the hash does not move.

Revision ID: c7a4e1b93d60
Revises: 5a1d2c7e9f30
Create Date: 2026-10-15

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c7a4e1b93d60'
down_revision = '5a1d2c7e9f30'
branch_labels = None
depends_on = None


def _identifier_helpers():
    """Imported lazily so collecting this module never needs app config."""
    from src.utilities import (decrypt_identifier, encrypt_identifier,
                               hash_identifier)
    return decrypt_identifier, encrypt_identifier, hash_identifier


def upgrade():
    op.add_column('kycs', sa.Column(
        'bvn_hash', sa.String(length=64), nullable=True))
    op.add_column('kycs', sa.Column(
        'nin_hash', sa.String(length=64), nullable=True))

    # IF EXISTS: these are the Postgres-generated names, confirmed on both the
    # local and production databases, but an environment that never had them
    # must not fail the upgrade.
    op.execute('ALTER TABLE kycs DROP CONSTRAINT IF EXISTS kycs_bvn_key')
    op.execute('ALTER TABLE kycs DROP CONSTRAINT IF EXISTS kycs_nin_key')

    decrypt_identifier, encrypt_identifier, hash_identifier = \
        _identifier_helpers()

    conn = op.get_bind()
    rows = conn.execute(sa.text(
        'SELECT id, bvn, nin FROM kycs '
        'WHERE bvn IS NOT NULL OR nin IS NOT NULL')).fetchall()

    for row in rows:
        record_id, bvn, nin = row[0], row[1], row[2]

        bvn_plain = decrypt_identifier(bvn)
        nin_plain = decrypt_identifier(nin)

        conn.execute(
            sa.text('UPDATE kycs SET bvn = :bvn, bvn_hash = :bvn_hash, '
                    'nin = :nin, nin_hash = :nin_hash WHERE id = :id'),
            {
                'bvn': encrypt_identifier(bvn_plain),
                'bvn_hash': hash_identifier(bvn_plain),
                'nin': encrypt_identifier(nin_plain),
                'nin_hash': hash_identifier(nin_plain),
                'id': record_id,
            })

    print(f'[migration] encrypted identifiers on {len(rows)} kyc row(s)')

    op.create_unique_constraint('kycs_bvn_hash_key', 'kycs', ['bvn_hash'])
    op.create_unique_constraint('kycs_nin_hash_key', 'kycs', ['nin_hash'])


def downgrade():
    """Restore plaintext and put uniqueness back on the value columns.

    This deliberately writes the identifiers back in the clear, because that is
    what the previous schema held. Only run it if you intend that.
    """
    decrypt_identifier, _encrypt, _hash = _identifier_helpers()

    conn = op.get_bind()
    rows = conn.execute(sa.text(
        'SELECT id, bvn, nin FROM kycs '
        'WHERE bvn IS NOT NULL OR nin IS NOT NULL')).fetchall()

    for row in rows:
        conn.execute(
            sa.text('UPDATE kycs SET bvn = :bvn, nin = :nin WHERE id = :id'),
            {
                'bvn': decrypt_identifier(row[1]),
                'nin': decrypt_identifier(row[2]),
                'id': row[0],
            })

    op.drop_constraint('kycs_bvn_hash_key', 'kycs', type_='unique')
    op.drop_constraint('kycs_nin_hash_key', 'kycs', type_='unique')
    op.drop_column('kycs', 'nin_hash')
    op.drop_column('kycs', 'bvn_hash')

    op.create_unique_constraint('kycs_bvn_key', 'kycs', ['bvn'])
    op.create_unique_constraint('kycs_nin_key', 'kycs', ['nin'])
