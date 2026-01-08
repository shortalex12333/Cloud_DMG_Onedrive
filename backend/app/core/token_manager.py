"""OAuth token management with automatic refresh"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy.orm import Session
from msal import ConfidentialClientApplication
import logging

from app.config import settings
from app.core.encryption import get_encryption
from app.models.connection import OneDriveConnection

logger = logging.getLogger(__name__)


class TokenManager:
    """Manages OAuth token lifecycle including refresh"""

    def __init__(self):
        """Initialize MSAL client application"""
        self.client_app = ConfidentialClientApplication(
            client_id=settings.azure_client_id,
            client_credential=settings.azure_client_secret,
            authority=f"https://login.microsoftonline.com/{settings.azure_tenant_id}"
        )
        self.encryption = get_encryption()

    def store_tokens(
        self,
        db: Session,
        yacht_id: str,
        user_principal_name: str,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ) -> OneDriveConnection:
        """
        Store OAuth tokens encrypted in database

        Args:
            db: Database session
            yacht_id: Yacht identifier
            user_principal_name: Microsoft user email
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiry in seconds

        Returns:
            OneDriveConnection record
        """
        # Calculate expiry time
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        # Encrypt tokens
        access_token_encrypted = self.encryption.encrypt_token(access_token)
        refresh_token_encrypted = self.encryption.encrypt_token(refresh_token)

        # Check if connection exists
        connection = db.query(OneDriveConnection).filter(
            OneDriveConnection.yacht_id == yacht_id,
            OneDriveConnection.user_principal_name == user_principal_name
        ).first()

        if connection:
            # Update existing connection
            connection.access_token_encrypted = access_token_encrypted
            connection.refresh_token_encrypted = refresh_token_encrypted
            connection.token_expires_at = token_expires_at
            connection.sync_enabled = True
            logger.info(f"Updated tokens for yacht {yacht_id}, user {user_principal_name}")
        else:
            # Create new connection
            connection = OneDriveConnection(
                yacht_id=yacht_id,
                user_principal_name=user_principal_name,
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                token_expires_at=token_expires_at,
                sync_enabled=True
            )
            db.add(connection)
            logger.info(f"Created new connection for yacht {yacht_id}, user {user_principal_name}")

        db.commit()
        db.refresh(connection)
        return connection

    def get_access_token(
        self,
        db: Session,
        connection_id: str
    ) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary

        Args:
            db: Database session
            connection_id: Connection UUID

        Returns:
            Valid access token or None if refresh fails
        """
        connection = db.query(OneDriveConnection).filter(
            OneDriveConnection.id == connection_id
        ).first()

        if not connection:
            logger.error(f"Connection {connection_id} not found")
            return None

        # Check if token is expired or expires within 5 minutes
        if datetime.utcnow() + timedelta(minutes=5) >= connection.token_expires_at:
            logger.info(f"Token expired or expiring soon for connection {connection_id}, refreshing...")
            return self.refresh_access_token(db, connection)

        # Token still valid, decrypt and return
        try:
            return self.encryption.decrypt_token(connection.access_token_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt access token: {e}")
            return None

    def refresh_access_token(
        self,
        db: Session,
        connection: OneDriveConnection
    ) -> Optional[str]:
        """
        Refresh access token using refresh token

        Args:
            db: Database session
            connection: OneDriveConnection record

        Returns:
            New access token or None if refresh fails
        """
        try:
            # Decrypt refresh token
            refresh_token = self.encryption.decrypt_token(connection.refresh_token_encrypted)

            # Request new tokens from Microsoft
            result = self.client_app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=settings.azure_scopes
            )

            if "error" in result:
                logger.error(f"Token refresh failed: {result.get('error_description')}")
                return None

            # Update tokens in database
            access_token = result["access_token"]
            new_refresh_token = result.get("refresh_token", refresh_token)  # May not always get new refresh token
            expires_in = result.get("expires_in", 3600)

            connection.access_token_encrypted = self.encryption.encrypt_token(access_token)
            connection.refresh_token_encrypted = self.encryption.encrypt_token(new_refresh_token)
            connection.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

            db.commit()
            logger.info(f"Successfully refreshed token for connection {connection.id}")

            return access_token

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    def revoke_connection(
        self,
        db: Session,
        connection_id: str
    ) -> bool:
        """
        Revoke connection and delete tokens

        Args:
            db: Database session
            connection_id: Connection UUID

        Returns:
            True if successful, False otherwise
        """
        try:
            connection = db.query(OneDriveConnection).filter(
                OneDriveConnection.id == connection_id
            ).first()

            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return False

            # Delete connection (cascade will delete sync state and jobs)
            db.delete(connection)
            db.commit()

            logger.info(f"Revoked connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke connection: {e}")
            db.rollback()
            return False


# Global instance
_token_manager = None

def get_token_manager() -> TokenManager:
    """Get global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
