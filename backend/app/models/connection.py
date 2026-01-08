"""OneDrive connection model"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class OneDriveConnection(Base):
    """OneDrive OAuth connection for a yacht"""
    __tablename__ = "onedrive_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    yacht_id = Column(String, nullable=False, index=True)
    user_principal_name = Column(String, nullable=False)  # Microsoft user email
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    sync_enabled = Column(Boolean, default=True)
    selected_folders = Column(JSONB, default=list)  # List of folder paths to sync
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_sync_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint('yacht_id', 'user_principal_name', name='uq_yacht_user'),
    )
