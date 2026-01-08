"""OAuth 2.0 authentication endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
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
    request: ConnectRequest,
    db: Session = Depends(get_db)
):
    """
    Initiate OAuth 2.0 flow for OneDrive connection

    Returns authorization URL for user to grant permissions
    """
    try:
        token_manager = get_token_manager()

        # Generate authorization URL with state parameter (yacht_id)
        auth_url = token_manager.client_app.get_authorization_request_url(
            scopes=settings.azure_scopes,
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
    code: str = Query(..., description="Authorization code from Microsoft"),
    state: str = Query(..., description="State parameter (yacht_id)"),
    db: Session = Depends(get_db)
):
    """
    OAuth 2.0 callback endpoint

    Exchanges authorization code for access token and stores in database
    """
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
            db=db,
            yacht_id=yacht_id,
            user_principal_name=user_principal_name,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )

        logger.info(f"Successfully connected OneDrive for yacht {yacht_id}, user {user_principal_name}")

        # Redirect to frontend dashboard
        frontend_url = settings.cors_origins[0]  # First CORS origin is frontend
        return RedirectResponse(
            url=f"{frontend_url}/dashboard?connected=true&connection_id={connection.id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")


@router.get("/status", response_model=ConnectionStatus)
async def get_connection_status(
    yacht_id: str = Query(..., description="Yacht ID"),
    db: Session = Depends(get_db)
):
    """
    Get OneDrive connection status for a yacht

    Returns connection details if connected
    """
    try:
        repo = ConnectionRepository(db)
        connections = repo.get_by_yacht_id(yacht_id)

        if not connections:
            return ConnectionStatus(connected=False)

        # Return first active connection
        connection = connections[0]

        return ConnectionStatus(
            connected=True,
            user_principal_name=connection.user_principal_name,
            connection_id=str(connection.id),
            sync_enabled=connection.sync_enabled
        )

    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/disconnect")
async def disconnect_onedrive(
    connection_id: str = Query(..., description="Connection ID"),
    db: Session = Depends(get_db)
):
    """
    Disconnect OneDrive and revoke tokens

    Deletes connection and all associated sync data
    """
    try:
        token_manager = get_token_manager()

        success = token_manager.revoke_connection(db, connection_id)

        if not success:
            raise HTTPException(status_code=404, detail="Connection not found")

        logger.info(f"Successfully disconnected connection {connection_id}")

        return {"success": True, "message": "OneDrive disconnected successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disconnect: {e}")
        raise HTTPException(status_code=500, detail=f"Disconnect failed: {str(e)}")


@router.get("/test-token")
async def test_token(
    connection_id: str = Query(..., description="Connection ID"),
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify token refresh works

    Returns user profile from Microsoft Graph
    """
    try:
        token_manager = get_token_manager()

        # This will automatically refresh if needed
        access_token = token_manager.get_access_token(db, connection_id)

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
