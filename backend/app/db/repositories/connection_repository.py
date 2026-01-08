"""Repository for OneDrive connection management"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.connection import OneDriveConnection


class ConnectionRepository:
    """Database operations for OneDrive connections"""

    def __init__(self, db: Session):
        """
        Initialize repository

        Args:
            db: Database session
        """
        self.db = db

    def get_by_id(self, connection_id: str) -> Optional[OneDriveConnection]:
        """Get connection by ID"""
        return self.db.query(OneDriveConnection).filter(
            OneDriveConnection.id == connection_id
        ).first()

    def get_by_yacht_id(self, yacht_id: str) -> List[OneDriveConnection]:
        """Get all connections for a yacht"""
        return self.db.query(OneDriveConnection).filter(
            OneDriveConnection.yacht_id == yacht_id
        ).all()

    def get_by_yacht_and_user(
        self,
        yacht_id: str,
        user_principal_name: str
    ) -> Optional[OneDriveConnection]:
        """Get connection by yacht ID and user email"""
        return self.db.query(OneDriveConnection).filter(
            OneDriveConnection.yacht_id == yacht_id,
            OneDriveConnection.user_principal_name == user_principal_name
        ).first()

    def get_active_connections(self) -> List[OneDriveConnection]:
        """Get all active (sync enabled) connections"""
        return self.db.query(OneDriveConnection).filter(
            OneDriveConnection.sync_enabled == True
        ).all()

    def update_selected_folders(
        self,
        connection_id: str,
        folder_paths: List[str]
    ) -> Optional[OneDriveConnection]:
        """Update selected folders for syncing"""
        connection = self.get_by_id(connection_id)
        if connection:
            connection.selected_folders = folder_paths
            self.db.commit()
            self.db.refresh(connection)
        return connection

    def disable_sync(self, connection_id: str) -> Optional[OneDriveConnection]:
        """Disable sync for a connection"""
        connection = self.get_by_id(connection_id)
        if connection:
            connection.sync_enabled = False
            self.db.commit()
            self.db.refresh(connection)
        return connection

    def enable_sync(self, connection_id: str) -> Optional[OneDriveConnection]:
        """Enable sync for a connection"""
        connection = self.get_by_id(connection_id)
        if connection:
            connection.sync_enabled = True
            self.db.commit()
            self.db.refresh(connection)
        return connection

    def delete(self, connection_id: str) -> bool:
        """Delete a connection"""
        connection = self.get_by_id(connection_id)
        if connection:
            self.db.delete(connection)
            self.db.commit()
            return True
        return False
