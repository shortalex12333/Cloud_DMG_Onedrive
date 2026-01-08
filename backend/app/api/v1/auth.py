"""OAuth 2.0 authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import logging

from app.config import settings
from app.db.session import get_db
from app.core.token_manager import get_token_manager
from app.core.graph_client import create_graph_client
from app.db.repositories.connection_repository import ConnectionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectRequest(BaseModel):
    """Request to initiate OAuth connection"""
    yacht_id: str


class ConnectResponse(BaseModel):
    """Response with OAuth authorization URL"""
    auth_url: str
    state: str


class ConnectionStatus(BaseModel):
    """Connection status response"""
    connected: bool
    user_principal_name: Optional[str] = None
    connection_id: Optional[str] = None
    sync_enabled: Optional[bool] = None


@router.post("/connect", response_model=ConnectResponse)
async def connect_onedrive(
    request: ConnectRequest
):
    """
    Initiate OAuth 2.0 flow for OneDrive connection

    Returns authorization URL for user to grant permissions
    """
    try:
        token_manager = get_token_manager()

        # Get scopes as a fresh list
        scopes = list(settings.azure_scopes)
        logger.info(f"Scopes type: {type(scopes)}, value: {scopes}")

        # Generate authorization URL with state parameter (yacht_id)
        auth_url = token_manager.client_app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=settings.azure_redirect_uri,
            state=request.yacht_id  # Pass yacht_id as state
        )

        logger.info(f"Generated auth URL for yacht {request.yacht_id}")

        return ConnectResponse(
            auth_url=auth_url,
            state=request.yacht_id
        )

    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None, description="Authorization code from Microsoft"),
    state: Optional[str] = Query(None, description="State parameter (yacht_id)"),
    error: Optional[str] = Query(None, description="Error from OAuth provider"),
    error_description: Optional[str] = Query(None, description="Error description")
):
    """
    OAuth 2.0 callback endpoint

    Exchanges authorization code for access token and stores in database
    """
    # Handle OAuth errors (user cancelled, etc.)
    if error:
        logger.warning(f"OAuth error: {error} - {error_description}")
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"https://digest.celeste7.ai/dashboard?error={error}&error_description={error_description or 'Authentication cancelled'}"
        )

    # Validate required parameters
    if not code or not state:
        logger.error("Missing required parameters: code or state")
        return RedirectResponse(
            url="https://digest.celeste7.ai/dashboard?error=invalid_request&error_description=Missing required parameters"
        )

    try:
        token_manager = get_token_manager()
        yacht_id = state  # State contains yacht_id

        # Exchange authorization code for tokens
        result = token_manager.client_app.acquire_token_by_authorization_code(
            code=code,
            scopes=settings.azure_scopes,
            redirect_uri=settings.azure_redirect_uri
        )

        if "error" in result:
            error_desc = result.get("error_description", "Unknown error")
            logger.error(f"Token exchange failed: {error_desc}")
            raise HTTPException(status_code=400, detail=f"Authentication failed: {error_desc}")

        # Extract tokens
        access_token = result["access_token"]
        refresh_token = result["refresh_token"]
        expires_in = result.get("expires_in", 3600)

        # Get user profile from Microsoft Graph
        graph_client = create_graph_client(access_token)
        user_profile = graph_client.get_user_profile()
        user_principal_name = user_profile.get("userPrincipalName")

        if not user_principal_name:
            raise HTTPException(status_code=400, detail="Failed to retrieve user email")

        # Store tokens in database
        connection = token_manager.store_tokens(
            yacht_id=yacht_id,
            user_principal_name=user_principal_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )

        logger.info(f"Successfully connected OneDrive for yacht {yacht_id}, user {user_principal_name}")

        # Redirect to frontend dashboard
        connection_id = connection.get('id', '')
        return RedirectResponse(
            url=f"https://digest.celeste7.ai/dashboard?connected=true&connection_id={connection_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status(
    yacht_id: str = Query(..., description="Yacht ID")
):
    """
    Get OneDrive connection status for a yacht

    Returns connection details if connected
    """
    try:
        from app.db.supabase_client import get_supabase
        supabase = get_supabase()

        # Query connections using Supabase REST API
        result = supabase.table('onedrive_connections')\
            .select('*')\
            .eq('yacht_id', yacht_id)\
            .eq('sync_enabled', True)\
            .execute()

        if not result.data or len(result.data) == 0:
            return ConnectionStatus(connected=False)

        # Return first active connection
        connection = result.data[0]

        return ConnectionStatus(
            connected=True,
            user_principal_name=connection['user_principal_name'],
            connection_id=connection['id'],
            sync_enabled=connection['sync_enabled']
        )

    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/disconnect")
async def disconnect_onedrive(
    connection_id: str = Query(..., description="Connection ID")
):
    """
    Disconnect OneDrive and revoke tokens using Supabase REST API

    Deletes connection and all associated sync data
    """
    try:
        token_manager = get_token_manager()

        success = token_manager.revoke_connection(connection_id)

        if not success:
            raise HTTPException(status_code=404, detail="Connection not found")

        logger.info(f"Successfully disconnected connection {connection_id}")

        return {"success": True, "message": "OneDrive disconnected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


@router.get("/health-check")
async def connection_health_check(
    connection_id: str = Query(..., description="Connection ID")
):
    """
    Health check endpoint for connection watchdog

    Verifies connection is still valid and tokens can be refreshed.
    Can be polled periodically to detect connection issues early.

    Returns:
        - healthy: True if connection is valid and tokens work
        - token_valid: Whether current token is valid
        - can_refresh: Whether tokens can be refreshed
        - error: Error message if unhealthy
    """
    try:
        token_manager = get_token_manager()

        # Try to get access token (will refresh if needed)
        access_token = token_manager.get_access_token(connection_id)

        if not access_token:
            return {
                "healthy": False,
                "token_valid": False,
                "can_refresh": False,
                "error": "Failed to get valid access token - tokens may be revoked"
            }

        # Try to make a simple API call to verify token works
        try:
            graph_client = create_graph_client(access_token)
            user_profile = graph_client.get_user_profile()

            return {
                "healthy": True,
                "token_valid": True,
                "can_refresh": True,
                "user_email": user_profile.get("userPrincipalName"),
                "last_checked": datetime.utcnow().isoformat()
            }
        except Exception as graph_error:
            # Token exists but API call failed
            return {
                "healthy": False,
                "token_valid": False,
                "can_refresh": False,
                "error": f"Graph API call failed: {str(graph_error)}"
            }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "healthy": False,
            "token_valid": False,
            "can_refresh": False,
            "error": str(e)
        }


@router.get("/check-onedrive-ready")
async def check_onedrive_ready(
    connection_id: str = Query(..., description="Connection ID")
):
    """
    Check if OneDrive for Business is provisioned and ready to use

    Returns provisioning status and helpful instructions if not ready
    """
    try:
        token_manager = get_token_manager()
        access_token = token_manager.get_access_token(connection_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get valid token")

        graph_client = create_graph_client(access_token)

        # Try to check OneDrive provisioning
        try:
            drive_info = graph_client.check_onedrive_provisioned()
            return {
                "ready": True,
                "drive_type": drive_info.get("driveType"),
                "owner": drive_info.get("owner", {}).get("user", {}).get("displayName"),
                "message": "OneDrive is provisioned and ready to use"
            }
        except Exception as provision_error:
            error_msg = str(provision_error)

            # Check if it's a provisioning issue
            if "not provisioned" in error_msg.lower() or "personal site" in error_msg.lower():
                return {
                    "ready": False,
                    "error": error_msg,
                    "instructions": [
                        "1. Go to https://office.com and sign in",
                        "2. Click the OneDrive icon/tile",
                        "3. Wait 10-15 minutes for OneDrive to be set up",
                        "4. Refresh this page and try again"
                    ]
                }

            # Other error
            raise HTTPException(status_code=502, detail=f"OneDrive check failed: {error_msg}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OneDrive ready check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")


@router.get("/test-token")
async def test_token(
    connection_id: str = Query(..., description="Connection ID")
):
    """
    Test endpoint to verify token refresh works using Supabase REST API

    Returns user profile from Microsoft Graph
    """
    try:
        token_manager = get_token_manager()

        # This will automatically refresh if needed
        access_token = token_manager.get_access_token(connection_id)

        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get valid token")

        # Test token by getting user profile
        graph_client = create_graph_client(access_token)
        user_profile = graph_client.get_user_profile()

        return {
            "success": True,
            "user": user_profile.get("displayName"),
            "email": user_profile.get("userPrincipalName")
        }

    except Exception as e:
        logger.error(f"Token test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Token test failed: {str(e)}")
