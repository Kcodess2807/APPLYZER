"""Add skills, education, and experience tables

Revision ID: 002
Revises: 001
Create Date: 2024-03-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('items', postgresql.ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('display_order', sa.Integer, nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_skills_id', 'skills', ['id'])
    op.create_index('ix_skills_user_id', 'skills', ['user_id'])
    
    # Create education table
    op.create_table(
        'education',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('degree', sa.String(255), nullable=False),
        sa.Column('institution', sa.String(255), nullable=False),
        sa.Column('year', sa.String(50), nullable=False),
        sa.Column('coursework', sa.String(500), nullable=True),
        sa.Column('display_order', sa.Integer, nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_education_id', 'education', ['id'])
    op.create_index('ix_education_user_id', 'education', ['user_id'])
    
    # Create experiences table
    op.create_table(
        'experiences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role', sa.String(255), nullable=False),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('duration', sa.String(100), nullable=False),
        sa.Column('achievements', postgresql.ARRAY(sa.String), nullable=False, server_default='{}'),
        sa.Column('display_order', sa.Integer, nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_experiences_id', 'experiences', ['id'])
    op.create_index('ix_experiences_user_id', 'experiences', ['user_id'])


def downgrade():
    op.drop_index('ix_experiences_user_id', 'experiences')
    op.drop_index('ix_experiences_id', 'experiences')
    op.drop_table('experiences')
    
    op.drop_index('ix_education_user_id', 'education')
    op.drop_index('ix_education_id', 'education')
    op.drop_table('education')
    
    op.drop_index('ix_skills_user_id', 'skills')
    op.drop_index('ix_skills_id', 'skills')
    op.drop_table('skills')
