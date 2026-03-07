"""Add missing columns to projects table

Revision ID: 005
Revises: 004
Create Date: 2024-03-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS category VARCHAR(100)")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS skills_demonstrated VARCHAR[] NOT NULL DEFAULT '{}'")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS keywords VARCHAR[] DEFAULT '{}'")


def downgrade():
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS keywords")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS skills_demonstrated")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS category")
