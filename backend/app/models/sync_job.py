"""OneDrive sync job model"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class OneDriveSyncJob(Base):
    """Sync job tracking for batch operations"""
    __tablename__ = "onedrive_sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey('onedrive_connections.id', ondelete='CASCADE'), nullable=False)
    yacht_id = Column(String, nullable=False, index=True)
    job_status = Column(String, nullable=False, default='pending')  # pending, running, completed, failed
    total_files_found = Column(Integer, default=0)
    files_succeeded = Column(Integer, default=0)
    files_failed = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
