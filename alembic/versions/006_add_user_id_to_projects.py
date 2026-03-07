"""Add user_id column to projects table

Revision ID: 006
Revises: 005
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa

revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS user_id UUID")
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_projects_user_id'
                  AND table_name = 'projects'
            ) THEN
                ALTER TABLE projects
                    ADD CONSTRAINT fk_projects_user_id
                    FOREIGN KEY (user_id) REFERENCES users(id);
            END IF;
        END $$
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id)
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_projects_user_id")
    op.execute("ALTER TABLE projects DROP CONSTRAINT IF EXISTS fk_projects_user_id")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS user_id")
