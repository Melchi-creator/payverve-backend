"""merge main's migration history with the BellBank branch's

Both lines start from 2129b3c36f79. main added 0be891a8b1b3 (account columns
on wallets), and production was last migrated from main, so its
alembic_version is 0be891a8b1b3. The BellBank branch added ce013ef17e3e ->
232def76afd1 -> fad65255d675 -> b7e4c19af820 instead, and did not have main's
file at all, so `flask db upgrade` failed with "Can't locate revision
identified by '0be891a8b1b3'".

This joins the two. Upgrading production from 0be891a8b1b3 runs the branch's
four migrations, which check what already exists before changing anything,
because some of their changes (fcm_token, at least) were already live there.

Revision ID: 5a1d2c7e9f30
Revises: 0be891a8b1b3, b7e4c19af820
Create Date: 2026-10-09

"""

# revision identifiers, used by Alembic.
revision = '5a1d2c7e9f30'
down_revision = ('0be891a8b1b3', 'b7e4c19af820')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
