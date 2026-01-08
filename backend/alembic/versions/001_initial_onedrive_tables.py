"""Initial OneDrive tables

Revision ID: 001
Revises:
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create onedrive_connections table
    op.create_table(
        'onedrive_connections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('yacht_id', sa.String(), nullable=False),
        sa.Column('user_principal_name', sa.String(), nullable=False),
        sa.Column('access_token_encrypted', sa.Text(), nullable=False),
        sa.Column('refresh_token_encrypted', sa.Text(), nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sync_enabled', sa.Boolean(), server_default='true'),
        sa.Column('selected_folders', JSONB, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('last_sync_at', sa.DateTime(timezone=True)),
        sa.UniqueConstraint('yacht_id', 'user_principal_name', name='uq_yacht_user')
    )
    op.create_index('ix_onedrive_connections_yacht_id', 'onedrive_connections', ['yacht_id'])

    # Create onedrive_sync_state table
    op.create_table(
        'onedrive_sync_state',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', UUID(as_uuid=True), nullable=False),
        sa.Column('yacht_id', sa.String(), nullable=False),
        sa.Column('onedrive_item_id', sa.String(), nullable=False),
        sa.Column('onedrive_path', sa.Text(), nullable=False),
        sa.Column('file_name', sa.String(), nullable=False),
        sa.Column('file_size', sa.BigInteger()),
        sa.Column('onedrive_etag', sa.String()),
        sa.Column('sync_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('supabase_doc_id', UUID(as_uuid=True)),
        sa.Column('extracted_metadata', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['connection_id'], ['onedrive_connections.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('connection_id', 'onedrive_item_id', name='uq_connection_item')
    )
    op.create_index('ix_onedrive_sync_state_yacht_id', 'onedrive_sync_state', ['yacht_id'])

    # Create onedrive_sync_jobs table
    op.create_table(
        'onedrive_sync_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('connection_id', UUID(as_uuid=True), nullable=False),
        sa.Column('yacht_id', sa.String(), nullable=False),
        sa.Column('job_status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('total_files_found', sa.Integer(), server_default='0'),
        sa.Column('files_succeeded', sa.Integer(), server_default='0'),
        sa.Column('files_failed', sa.Integer(), server_default='0'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['connection_id'], ['onedrive_connections.id'], ondelete='CASCADE')
    )
    op.create_index('ix_onedrive_sync_jobs_yacht_id', 'onedrive_sync_jobs', ['yacht_id'])


def downgrade() -> None:
    op.drop_table('onedrive_sync_jobs')
    op.drop_table('onedrive_sync_state')
    op.drop_table('onedrive_connections')
