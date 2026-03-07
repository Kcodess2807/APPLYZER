"""Add Gmail and Sheets tracking to applications

Revision ID: 003
Revises: 002
Create Date: 2024-03-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to applications table
    op.add_column('applications', sa.Column('cover_letter_path', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('gmail_message_id', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('gmail_thread_id', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('email_sent_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('applications', sa.Column('reply_received', sa.String(10), nullable=False, server_default='false'))
    op.add_column('applications', sa.Column('reply_received_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('applications', sa.Column('followup_count', sa.String(10), nullable=False, server_default='0'))
    op.add_column('applications', sa.Column('last_followup_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('applications', sa.Column('sheets_row_id', sa.String(50), nullable=True))
    
    # Create indexes
    op.create_index('ix_applications_gmail_message_id', 'applications', ['gmail_message_id'])
    op.create_index('ix_applications_gmail_thread_id', 'applications', ['gmail_thread_id'])


def downgrade():
    op.drop_index('ix_applications_gmail_thread_id', 'applications')
    op.drop_index('ix_applications_gmail_message_id', 'applications')
    
    op.drop_column('applications', 'sheets_row_id')
    op.drop_column('applications', 'last_followup_at')
    op.drop_column('applications', 'followup_count')
    op.drop_column('applications', 'reply_received_at')
    op.drop_column('applications', 'reply_received')
    op.drop_column('applications', 'email_sent_at')
    op.drop_column('applications', 'gmail_thread_id')
    op.drop_column('applications', 'gmail_message_id')
    op.drop_column('applications', 'cover_letter_path')
