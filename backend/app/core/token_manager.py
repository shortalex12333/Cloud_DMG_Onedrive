"""OAuth token management with automatic refresh and timezone handling"""
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
        """Initialize MSAL client application for multi-tenant access"""
        # Use /common endpoint to allow users from any Azure AD tenant
        # This enables yacht clients to authenticate with their own Microsoft 365 accounts
        self.client_app = ConfidentialClientApplication(
            client_id=settings.azure_client_id,
            client_credential=settings.azure_client_secret,
            authority="https://login.microsoftonline.com/common"
        )
        self.encryption = get_encryption()

    def store_tokens(
        self,
        yacht_id: str,
        user_principal_name: str,
        access_token: str,
        refresh_token: str,
        expires_in: int
    ) -> dict:
        """
        Store OAuth tokens encrypted in database using Supabase REST API

        Args:
            yacht_id: Yacht identifier
            user_principal_name: Microsoft user email
            access_token: OAuth access token
            refresh_token: OAuth refresh token
            expires_in: Token expiry in seconds

        Returns:
            Connection record dict
        """
        from app.db.supabase_client import get_supabase

        # Calculate expiry time
        token_expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

        # Encrypt tokens
        access_token_encrypted = self.encryption.encrypt_token(access_token)
        refresh_token_encrypted = self.encryption.encrypt_token(refresh_token)

        supabase = get_supabase()

        # Check if connection exists
        result = supabase.table('onedrive_connections')\
            .select('*')\
            .eq('yacht_id', yacht_id)\
            .eq('user_principal_name', user_principal_name)\
            .execute()

        if result.data and len(result.data) > 0:
            # Update existing connection
            connection_id = result.data[0]['id']
            updated = supabase.table('onedrive_connections')\
                .update({
                    'access_token_encrypted': access_token_encrypted,
                    'refresh_token_encrypted': refresh_token_encrypted,
                    'token_expires_at': token_expires_at,
                    'sync_enabled': True,
                    'last_sync_at': datetime.utcnow().isoformat()
                })\
                .eq('id', connection_id)\
                .execute()
            logger.info(f"Updated tokens for yacht {yacht_id}, user {user_principal_name}")
            return updated.data[0] if updated.data else {}
        else:
            # Create new connection
            new_connection = supabase.table('onedrive_connections')\
                .insert({
                    'yacht_id': yacht_id,
                    'user_principal_name': user_principal_name,
                    'access_token_encrypted': access_token_encrypted,
                    'refresh_token_encrypted': refresh_token_encrypted,
                    'token_expires_at': token_expires_at,
                    'sync_enabled': True
                })\
                .execute()
            logger.info(f"Created new connection for yacht {yacht_id}, user {user_principal_name}")
            return new_connection.data[0] if new_connection.data else {}

    def get_access_token(
        self,
        connection_id: str
    ) -> Optional[str]:
        """
        Get valid access token, refreshing if necessary using Supabase REST API

        Args:
            connection_id: Connection UUID

        Returns:
            Valid access token or None if refresh fails
        """
        logger.info(f"[TOKEN_MANAGER] get_access_token called for connection {connection_id}")

        from app.db.supabase_client import get_supabase
        from dateutil import parser
        import time

        supabase = get_supabase()

        # Get connection
        logger.info(f"[TOKEN_MANAGER] Fetching connection from Supabase...")
        result = supabase.table('onedrive_connections')\
            .select('*')\
            .eq('id', connection_id)\
            .execute()

        if not result.data or len(result.data) == 0:
            logger.error(f"Connection {connection_id} not found")
            return None

        connection = result.data[0]
        logger.info(f"[TOKEN_MANAGER] Connection found. token_expires_at raw value: {connection.get('token_expires_at')}")

        # Check if token is expired or expires within 5 minutes
        # Use Unix timestamps to avoid timezone comparison issues
        try:
            logger.info(f"[TOKEN_MANAGER] Parsing expiry timestamp...")
            # Parse token expiry time and convert to Unix timestamp
            token_expires_at = parser.parse(connection['token_expires_at'])
            logger.info(f"[TOKEN_MANAGER] Parsed datetime: {token_expires_at}, tzinfo: {token_expires_at.tzinfo}")

            expiry_timestamp = token_expires_at.timestamp()
            logger.info(f"[TOKEN_MANAGER] Expiry Unix timestamp: {expiry_timestamp}")

            # Get current time as Unix timestamp (always UTC, no timezone issues)
            current_timestamp = time.time()
            logger.info(f"[TOKEN_MANAGER] Current Unix timestamp: {current_timestamp}")

            # Add 5 minutes buffer (300 seconds)
            if current_timestamp + 300 >= expiry_timestamp:
                logger.info(f"Token expired or expiring soon for connection {connection_id}, refreshing...")
                return self.refresh_access_token(connection)

            logger.info(f"[TOKEN_MANAGER] Token still valid, not expired")
        except Exception as e:
            # Catch ALL exceptions to see what's happening
            logger.error(f"[TOKEN_MANAGER] Exception during token expiry check: {type(e).__name__}: {e}", exc_info=True)
            logger.warning(f"DateTime handling error (assuming expired): {e}")
            return self.refresh_access_token(connection)

        # Token still valid, decrypt and return
        try:
            return self.encryption.decrypt_token(connection['access_token_encrypted'])
        except Exception as e:
            logger.error(f"Failed to decrypt access token: {e}")
            return None

    def refresh_access_token(
        self,
        connection: dict
    ) -> Optional[str]:
        """
        Refresh access token using refresh token via Supabase REST API

        Args:
            connection: Connection dict from Supabase

        Returns:
            New access token or None if refresh fails
        """
        from app.db.supabase_client import get_supabase

        try:
            # Decrypt refresh token
            refresh_token = self.encryption.decrypt_token(connection['refresh_token_encrypted'])

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
            token_expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

            access_token_encrypted = self.encryption.encrypt_token(access_token)
            refresh_token_encrypted = self.encryption.encrypt_token(new_refresh_token)

            # Update in Supabase
            supabase = get_supabase()
            supabase.table('onedrive_connections')\
                .update({
                    'access_token_encrypted': access_token_encrypted,
                    'refresh_token_encrypted': refresh_token_encrypted,
                    'token_expires_at': token_expires_at
                })\
                .eq('id', connection['id'])\
                .execute()

            logger.info(f"Successfully refreshed token for connection {connection['id']}")

            return access_token

        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            return None

    def revoke_connection(
        self,
        connection_id: str
    ) -> bool:
        """
        Revoke connection and delete tokens using Supabase REST API

        Args:
            connection_id: Connection UUID

        Returns:
            True if successful, False otherwise
        """
        from app.db.supabase_client import get_supabase

        try:
            supabase = get_supabase()

            # Check if connection exists
            result = supabase.table('onedrive_connections')\
                .select('id')\
                .eq('id', connection_id)\
                .execute()

            if not result.data or len(result.data) == 0:
                logger.error(f"Connection {connection_id} not found")
                return False

            # Delete connection (cascade should delete sync state and jobs)
            delete_result = supabase.table('onedrive_connections')\
                .delete()\
                .eq('id', connection_id)\
                .execute()

            logger.info(f"Revoked connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke connection: {e}")
            return False


# Global instance
_token_manager = None

def get_token_manager() -> TokenManager:
    """Get global token manager instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager
