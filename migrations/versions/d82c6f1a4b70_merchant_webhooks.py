"""merchant webhooks

Lets a shop be told when a charge is paid instead of polling for it.

merchants gains a webhook_url and a signing secret. The secret is encrypted,
not hashed, because unlike the API secret key we must recover the plaintext to
compute a signature.

webhook_deliveries records every attempt, so a notification a shop's server
rejected can be resent and a shop can ask later what we tried to send.

Revision ID: d82c6f1a4b70
Revises: c41f7a2b9e30
Create Date: 2026-11-09

"""
import sqlalchemy as sa
from alembic import op

revision = 'd82c6f1a4b70'
down_revision = 'c41f7a2b9e30'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('merchants',
                  sa.Column('webhook_url', sa.String(), nullable=True))
    op.add_column('merchants',
                  sa.Column('webhook_secret', sa.String(), nullable=True))

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('event', sa.String(), nullable=False),
        # Copied at enqueue so a later change of webhook_url cannot redirect
        # an event already queued.
        sa.Column('target_url', sa.String(), nullable=False),
        # The exact bytes signed and sent, frozen at enqueue.
        sa.Column('payload', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False,
                  server_default='pending'),
        sa.Column('attempts', sa.Integer(), nullable=False,
                  server_default='0'),
        sa.Column('last_status_code', sa.Integer(), nullable=True),
        sa.Column('last_error', sa.String(), nullable=True),
        sa.Column('next_attempt_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('merchant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('charge_id', sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['merchant_id'], ['merchants.id']),
        sa.ForeignKeyConstraint(['charge_id'], ['charges.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    # The retry job asks for pending deliveries that are due.
    op.create_index('ix_webhook_deliveries_due', 'webhook_deliveries',
                    ['status', 'next_attempt_at'])


def downgrade():
    op.drop_index('ix_webhook_deliveries_due',
                  table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_column('merchants', 'webhook_secret')
    op.drop_column('merchants', 'webhook_url')
