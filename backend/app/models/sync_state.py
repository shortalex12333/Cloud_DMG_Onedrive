"""OneDrive file sync state model"""
from sqlalchemy import Column, String, BigInteger, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class OneDriveSyncState(Base):
    """Per-file sync state tracking"""
    __tablename__ = "onedrive_sync_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey('onedrive_connections.id', ondelete='CASCADE'), nullable=False)
    yacht_id = Column(String, nullable=False, index=True)
    onedrive_item_id = Column(String, nullable=False)  # OneDrive file ID
    onedrive_path = Column(Text, nullable=False)  # Full path in OneDrive
    file_name = Column(String, nullable=False)
    file_size = Column(BigInteger)
    onedrive_etag = Column(String)  # OneDrive eTag for change detection
    sync_status = Column(String, nullable=False, default='pending')  # pending, syncing, completed, failed
    supabase_doc_id = Column(UUID(as_uuid=True))  # Reference to doc_metadata table
    extracted_metadata = Column(JSONB)  # doc_type, system_tag, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('connection_id', 'onedrive_item_id', name='uq_connection_item'),
    )
