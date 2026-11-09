"""merchants and charges

Adds the merchant layer: a shop that accepts payment through Payverve, and the
charges raised against it.

A merchant holds no money. Settlement goes to the owner's own NGN wallet, and
the account a buyer transfers to is the owner's BellBank virtual account, so
no new money-holding entity is introduced.

Revision ID: c41f7a2b9e30
Revises: c7a4e1b93d60
Create Date: 2026-11-09

"""
import sqlalchemy as sa
from alembic import op

revision = 'c41f7a2b9e30'
down_revision = 'c7a4e1b93d60'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'merchants',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('business_name', sa.String(), nullable=False),
        sa.Column('public_key', sa.String(), nullable=False),
        # The secret itself is never stored, only its keyed hash.
        sa.Column('secret_key_hash', sa.String(), nullable=False),
        sa.Column('secret_key_preview', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False,
                  server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('public_key'),
        sa.UniqueConstraint('secret_key_hash'),
    )

    op.create_table(
        'charges',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('reference', sa.String(), nullable=False),
        sa.Column('charge_code', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency_ticker', sa.String(), nullable=False,
                  server_default='ngn'),
        sa.Column('status', sa.String(), nullable=False,
                  server_default='pending'),
        sa.Column('method', sa.String(), nullable=True),
        sa.Column('callback_url', sa.String(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('settlement_reference', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('merchant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('charge_code'),
        # A shop retrying "create the charge for order 1234" must get the same
        # charge back, not a second one the buyer could also pay.
        sa.UniqueConstraint('merchant_id', 'reference',
                            name='uq_charges_merchant_reference'),
    )


def downgrade():
    op.drop_table('charges')
    op.drop_table('merchants')
