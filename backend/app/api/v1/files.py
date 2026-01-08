"""File browsing endpoints for OneDrive"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.db.session import get_db
from app.core.token_manager import get_token_manager
from app.core.graph_client import create_graph_client, GraphAPIError
from app.core.metadata_extractor import extract_metadata_from_onedrive_path

logger = logging.getLogger(__name__)

router = APIRouter()


class FileItem(BaseModel):
    """OneDrive file or folder item"""
    id: str
    name: str
    path: str
    is_folder: bool
    size: Optional[int] = None
    mime_type: Optional[str] = None
    created: Optional[str] = None
    modified: Optional[str] = None


class FileListResponse(BaseModel):
    """Response with list of files"""
    items: List[FileItem]
    path: str


class FileMetadata(BaseModel):
    """Extracted metadata from file path"""
    system_path: str
    directories: List[str]
    doc_type: str
    system_tag: str
    filename: str


@router.get("/browse", response_model=FileListResponse)
async def browse_onedrive(
    connection_id: str = Query(..., description="Connection ID"),
    path: str = Query("/", description="Folder path to browse"),
    db: Session = Depends(get_db)
):
    """
    Browse OneDrive files and folders

    Returns list of items in the specified path
    """
    try:
        token_manager = get_token_manager()

        # Get valid access token (auto-refreshes if needed)
        access_token = token_manager.get_access_token(db, connection_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get valid access token")

        # Create Graph client
        graph_client = create_graph_client(access_token)

        # List items in folder
        if path == "/" or path == "":
            items = graph_client.list_root_items()
        else:
            items = graph_client.list_folder_items(path)

        # Format response
        file_items = []
        for item in items:
            is_folder = "folder" in item
            file_items.append(FileItem(
                id=item["id"],
                name=item["name"],
                path=f"{path}/{item['name']}" if path != "/" else f"/{item['name']}",
                is_folder=is_folder,
                size=item.get("size"),
                mime_type=item.get("file", {}).get("mimeType") if not is_folder else None,
                created=item.get("createdDateTime"),
                modified=item.get("lastModifiedDateTime")
            ))

        return FileListResponse(items=file_items, path=path)

    except GraphAPIError as e:
        logger.error(f"Graph API error: {e}")
        raise HTTPException(status_code=502, detail=f"OneDrive API error: {str(e)}")
    except Exception as e:
        logger.error(f"Browse failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to browse: {str(e)}")


@router.get("/search")
async def search_onedrive(
    connection_id: str = Query(..., description="Connection ID"),
    query: str = Query(..., description="Search query"),
    db: Session = Depends(get_db)
):
    """
    Search for files in OneDrive

    Returns list of matching files
    """
    try:
        token_manager = get_token_manager()

        # Get valid access token
        access_token = token_manager.get_access_token(db, connection_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get valid access token")

        # Create Graph client
        graph_client = create_graph_client(access_token)

        # Search files
        results = graph_client.search_files(query)

        # Format response
        file_items = []
        for item in results:
            is_folder = "folder" in item
            if not is_folder:  # Only return files, not folders
                file_items.append(FileItem(
                    id=item["id"],
                    name=item["name"],
                    path=item.get("parentReference", {}).get("path", ""),
                    is_folder=False,
                    size=item.get("size"),
                    mime_type=item.get("file", {}).get("mimeType"),
                    created=item.get("createdDateTime"),
                    modified=item.get("lastModifiedDateTime")
                ))

        return {"items": file_items, "query": query, "count": len(file_items)}

    except GraphAPIError as e:
        logger.error(f"Graph API error: {e}")
        raise HTTPException(status_code=502, detail=f"OneDrive API error: {str(e)}")
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/metadata", response_model=FileMetadata)
async def get_file_metadata(
    path: str = Query(..., description="File path in OneDrive")
):
    """
    Extract metadata from OneDrive file path

    Returns doc_type, system_tag, etc. based on folder structure
    """
    try:
        metadata = extract_metadata_from_onedrive_path(path)

        return FileMetadata(
            system_path=metadata['system_path'],
            directories=metadata['directories'],
            doc_type=metadata['doc_type'],
            system_tag=metadata['system_tag'],
            filename=metadata['filename']
        )

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to extract metadata: {str(e)}")


@router.post("/enumerate")
async def enumerate_folders(
    connection_id: str = Query(..., description="Connection ID"),
    folder_paths: List[str] = Query(..., description="List of folder paths to enumerate"),
    recursive: bool = Query(True, description="Recursively scan subfolders"),
    db: Session = Depends(get_db)
):
    """
    Enumerate all files in specified folders

    Returns comprehensive list of all files found
    """
    try:
        token_manager = get_token_manager()

        # Get valid access token
        access_token = token_manager.get_access_token(db, connection_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get valid access token")

        # Create Graph client
        graph_client = create_graph_client(access_token)

        # Enumerate all files
        all_files = graph_client.enumerate_all_files(folder_paths, recursive)

        return {
            "total_files": len(all_files),
            "files": all_files,
            "folder_paths": folder_paths,
            "recursive": recursive
        }

    except GraphAPIError as e:
        logger.error(f"Graph API error: {e}")
        raise HTTPException(status_code=502, detail=f"OneDrive API error: {str(e)}")
    except Exception as e:
        logger.error(f"Enumeration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enumerate: {str(e)}")
