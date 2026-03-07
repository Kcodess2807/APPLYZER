"""Add job_roles column to projects table

Revision ID: 004
Revises: 003
Create Date: 2024-03-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'projects',
        sa.Column(
            'job_roles',
            ARRAY(sa.String),
            nullable=False,
            server_default='{}',
        )
    )


def downgrade():
    op.drop_column('projects', 'job_roles')
