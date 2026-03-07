"""Initial migration with core tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('linkedin_url', sa.String(length=255), nullable=True),
    sa.Column('github_url', sa.String(length=255), nullable=True),
    sa.Column('professional_summary', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create jobs table
    op.create_table('jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('company', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.Column('salary_range', sa.String(length=100), nullable=True),
    sa.Column('requirements', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('application_email', sa.String(length=255), nullable=True),
    sa.Column('source', sa.String(length=100), nullable=False),
    sa.Column('external_id', sa.String(length=255), nullable=True),
    sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'], unique=False)
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_location'), 'jobs', ['location'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)

    # Create projects table
    op.create_table('projects',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('duration', sa.String(length=100), nullable=True),
    sa.Column('project_type', sa.String(length=100), nullable=True),
    sa.Column('technologies', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('achievements', postgresql.ARRAY(sa.String()), nullable=False),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('project_url', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)

    # Create applications table
    op.create_table('applications',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('resume_path', sa.String(length=255), nullable=True),
    sa.Column('cover_letter', sa.Text(), nullable=True),
    sa.Column('email_subject', sa.String(length=255), nullable=True),
    sa.Column('email_body', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('response_received_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('follow_up_scheduled_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_batch_id'), 'applications', ['batch_id'], unique=False)
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'], unique=False)
    op.create_index(op.f('ix_applications_job_id'), 'applications', ['job_id'], unique=False)
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'], unique=False)
    op.create_index(op.f('ix_applications_user_id'), 'applications', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('applications')
    op.drop_table('projects')
    op.drop_table('jobs')
    op.drop_table('users')