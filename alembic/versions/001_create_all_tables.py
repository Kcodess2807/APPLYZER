"""Create all application tables with complete schema.

Revision ID: 001_create_all_tables
Revises: 
Create Date: 2026-03-07

This migration creates the complete database schema for APPLYZER including:
- profiles: User identity, skills, education, and experience
- jobs: Fetched job listings
- applications: Job application tracking with email and reply tracking
- projects: GitHub-synced projects enriched with LLM analysis
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_all_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create profiles table ───────────────────────────────────────────────────
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('github_username', sa.String(length=100), nullable=True),
        sa.Column('professional_summary', sa.Text(), nullable=True),
        sa.Column('experience_years', sa.String(length=20), nullable=True),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('education', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('experience', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_profiles_email'), 'profiles', ['email'], unique=True)
    op.create_index(op.f('ix_profiles_id'), 'profiles', ['id'])

    # ── Create jobs table ──────────────────────────────────────────────────────
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('salary_range', sa.String(length=100), nullable=True),
        sa.Column('requirements', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('technologies', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('application_email', sa.String(length=255), nullable=True),
        sa.Column('job_url', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('posted_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'])
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'])
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'])
    op.create_index(op.f('ix_jobs_location'), 'jobs', ['location'])

    # ── Create applications table ──────────────────────────────────────────────
    op.create_table(
        'applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('batch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resume_path', sa.String(length=255), nullable=True),
        sa.Column('cover_letter_path', sa.String(length=255), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('email_subject', sa.String(length=255), nullable=True),
        sa.Column('email_body', sa.Text(), nullable=True),
        sa.Column('gmail_message_id', sa.String(length=255), nullable=True),
        sa.Column('gmail_thread_id', sa.String(length=255), nullable=True),
        sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reply_received', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reply_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('followup_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_followup_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sheets_row_id', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('follow_up_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_applications_id'), 'applications', ['id'])
    op.create_index(op.f('ix_applications_profile_id'), 'applications', ['profile_id'])
    op.create_index(op.f('ix_applications_job_id'), 'applications', ['job_id'])
    op.create_index(op.f('ix_applications_batch_id'), 'applications', ['batch_id'])
    op.create_index(op.f('ix_applications_gmail_message_id'), 'applications', ['gmail_message_id'])
    op.create_index(op.f('ix_applications_status'), 'applications', ['status'])

    # ── Create projects table ──────────────────────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('github_repo_name', sa.String(length=255), nullable=False),
        sa.Column('github_repo_url', sa.String(length=500), nullable=False),
        sa.Column('primary_language', sa.String(length=100), nullable=True),
        sa.Column('github_topics', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('github_stars', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('github_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tech_stack', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('features', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('resume_bullets', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('skills_demonstrated', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('llm_processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('readme_raw', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'])
    op.create_index(op.f('ix_projects_profile_id'), 'projects', ['profile_id'])


def downgrade() -> None:
    # ── Drop tables in reverse order (respecting foreign keys) ──────────────────
    op.drop_index(op.f('ix_projects_profile_id'), table_name='projects')
    op.drop_index(op.f('ix_projects_id'), table_name='projects')
    op.drop_table('projects')

    op.drop_index(op.f('ix_applications_status'), table_name='applications')
    op.drop_index(op.f('ix_applications_gmail_message_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_batch_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_job_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_profile_id'), table_name='applications')
    op.drop_index(op.f('ix_applications_id'), table_name='applications')
    op.drop_table('applications')

    op.drop_index(op.f('ix_jobs_location'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')

    op.drop_index(op.f('ix_profiles_id'), 'profiles')
    op.drop_index(op.f('ix_profiles_email'), 'profiles')
    op.drop_table('profiles')
