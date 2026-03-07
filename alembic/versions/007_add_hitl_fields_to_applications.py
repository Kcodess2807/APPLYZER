"""Add HITL approval/rejection fields to applications table

Revision ID: 007
Revises: 006
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa

revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE applications
            ADD COLUMN IF NOT EXISTS approved_at   TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS rejected_at   TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS rejection_reason TEXT
    """)
    # Extend status enum-like values (column is VARCHAR, so no enum DDL needed)


def downgrade():
    op.execute("""
        ALTER TABLE applications
            DROP COLUMN IF EXISTS approved_at,
            DROP COLUMN IF EXISTS rejected_at,
            DROP COLUMN IF EXISTS rejection_reason
    """)
