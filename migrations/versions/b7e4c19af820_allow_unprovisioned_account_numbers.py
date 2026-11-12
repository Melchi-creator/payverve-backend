"""allow a virtual account with no expiry

A static BellBank virtual account does not expire, so
virtual_account_numbers.account_expiration_datetime has to accept NULL.
Provisioning refuses to invent a value for it.

wallets.account_number is deliberately untouched: migration 2129b3c36f79 already
moved account details onto virtual_account_numbers, so wallets no longer carries
that column.

Revision ID: b7e4c19af820
Revises: fad65255d675
Create Date: 2026-08-19

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'b7e4c19af820'
down_revision = 'fad65255d675'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('virtual_account_numbers', 'account_expiration_datetime',
                    existing_type=sa.DateTime(),
                    nullable=True)


def downgrade():
    op.alter_column('virtual_account_numbers', 'account_expiration_datetime',
                    existing_type=sa.DateTime(),
                    nullable=False)
