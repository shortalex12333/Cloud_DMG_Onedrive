"""Sync management endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from app.db.session import get_db
from app.core.token_manager import get_token_manager
from app.core.sync_manager import SyncManager
from app.models.sync_job import OneDriveSyncJob
from app.models.sync_state import OneDriveSyncState
from app.db.repositories.connection_repository import ConnectionRepository

logger = logging.getLogger(__name__)

router = APIRouter()


class StartSyncRequest(BaseModel):
    """Request to start sync"""
    connection_id: str
    folder_paths: List[str]


class SyncJobStatus(BaseModel):
    """Sync job status response"""
    job_id: str
    job_status: str
    total_files_found: int
    files_succeeded: int
    files_failed: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class SyncFileState(BaseModel):
    """Individual file sync state"""
    file_name: str
    onedrive_path: str
    sync_status: str
    file_size: Optional[int]
    created_at: datetime


def perform_sync(
    job_id: str,
    connection_id: str,
    yacht_id: str,
    folder_paths: List[str],
    db: Session
):
    """
    Background task to perform sync operation

    Args:
        job_id: Sync job ID
        connection_id: OneDrive connection ID
        yacht_id: Yacht identifier
        folder_paths: List of folder paths to sync
        db: Database session
    """
    logger.info(f"Starting sync job {job_id}")

    sync_manager = SyncManager(db)
    token_manager = get_token_manager()

    try:
        # Update job to running
        job = db.query(OneDriveSyncJob).filter(OneDriveSyncJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.job_status = 'running'
        job.started_at = datetime.utcnow()
        db.commit()

        # Get valid access token
        access_token = token_manager.get_access_token(connection_id)
        if not access_token:
            logger.error(f"Failed to get access token for connection {connection_id}")
            sync_manager.complete_job(job_id, 'failed')
            return

        # Enumerate files
        logger.info(f"Enumerating files from {len(folder_paths)} folders")
        files = sync_manager.enumerate_files_for_sync(access_token, folder_paths)

        # Update job with total count
        job.total_files_found = len(files)
        db.commit()

        logger.info(f"Found {len(files)} files to sync")

        # Sync each file
        succeeded = 0
        failed = 0

        for file_info in files:
            try:
                success = sync_manager.sync_file(
                    access_token=access_token,
                    connection_id=connection_id,
                    yacht_id=yacht_id,
                    file_info=file_info,
                    job_id=job_id
                )

                if success:
                    succeeded += 1
                else:
                    failed += 1

                # Update progress
                sync_manager.update_job_progress(job_id, succeeded, failed)

            except Exception as e:
                logger.error(f"Failed to sync file: {e}")
                failed += 1
                sync_manager.update_job_progress(job_id, succeeded, failed)

        # Complete job
        sync_manager.complete_job(job_id, 'completed')

        logger.info(f"Sync job {job_id} completed: {succeeded} succeeded, {failed} failed")

        # Update last_sync_at on connection
        connection_repo = ConnectionRepository(db)
        connection = connection_repo.get_by_id(connection_id)
        if connection:
            connection.last_sync_at = datetime.utcnow()
            db.commit()

    except Exception as e:
        logger.error(f"Sync job {job_id} failed: {e}")
        sync_manager.complete_job(job_id, 'failed')


@router.post("/start", response_model=SyncJobStatus)
async def start_sync(
    request: StartSyncRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start a sync operation

    Creates sync job and processes files in background
    """
    try:
        # Verify connection exists
        connection_repo = ConnectionRepository(db)
        connection = connection_repo.get_by_id(request.connection_id)

        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")

        if not connection.sync_enabled:
            raise HTTPException(status_code=400, detail="Sync is disabled for this connection")

        # Update selected folders
        connection_repo.update_selected_folders(request.connection_id, request.folder_paths)

        # Create sync job
        sync_manager = SyncManager(db)
        job = sync_manager.create_sync_job(
            connection_id=request.connection_id,
            yacht_id=connection.yacht_id,
            folder_paths=request.folder_paths
        )

        # Start sync in background
        background_tasks.add_task(
            perform_sync,
            job_id=str(job.id),
            connection_id=request.connection_id,
            yacht_id=connection.yacht_id,
            folder_paths=request.folder_paths,
            db=db
        )

        logger.info(f"Started sync job {job.id} in background")

        return SyncJobStatus(
            job_id=str(job.id),
            job_status=job.job_status,
            total_files_found=job.total_files_found,
            files_succeeded=job.files_succeeded,
            files_failed=job.files_failed,
            started_at=job.started_at,
            completed_at=job.completed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start sync: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.get("/status", response_model=SyncJobStatus)
async def get_sync_status(
    job_id: str = Query(..., description="Sync job ID"),
    db: Session = Depends(get_db)
):
    """
    Get sync job status

    Returns current progress and status
    """
    try:
        job = db.query(OneDriveSyncJob).filter(OneDriveSyncJob.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Sync job not found")

        return SyncJobStatus(
            job_id=str(job.id),
            job_status=job.job_status,
            total_files_found=job.total_files_found,
            files_succeeded=job.files_succeeded,
            files_failed=job.files_failed,
            started_at=job.started_at,
            completed_at=job.completed_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get sync status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/history")
async def get_sync_history(
    connection_id: str = Query(..., description="Connection ID"),
    limit: int = Query(10, description="Max jobs to return"),
    db: Session = Depends(get_db)
):
    """
    Get sync history for a connection

    Returns list of recent sync jobs
    """
    try:
        jobs = db.query(OneDriveSyncJob).filter(
            OneDriveSyncJob.connection_id == connection_id
        ).order_by(OneDriveSyncJob.created_at.desc()).limit(limit).all()

        return {
            "jobs": [
                SyncJobStatus(
                    job_id=str(job.id),
                    job_status=job.job_status,
                    total_files_found=job.total_files_found,
                    files_succeeded=job.files_succeeded,
                    files_failed=job.files_failed,
                    started_at=job.started_at,
                    completed_at=job.completed_at
                ) for job in jobs
            ],
            "connection_id": connection_id
        }

    except Exception as e:
        logger.error(f"Failed to get sync history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/files")
async def get_synced_files(
    connection_id: str = Query(..., description="Connection ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, description="Max files to return"),
    db: Session = Depends(get_db)
):
    """
    Get list of synced files

    Returns files with their sync status
    """
    try:
        query = db.query(OneDriveSyncState).filter(
            OneDriveSyncState.connection_id == connection_id
        )

        if status:
            query = query.filter(OneDriveSyncState.sync_status == status)

        files = query.order_by(OneDriveSyncState.created_at.desc()).limit(limit).all()

        return {
            "files": [
                SyncFileState(
                    file_name=f.file_name,
                    onedrive_path=f.onedrive_path,
                    sync_status=f.sync_status,
                    file_size=f.file_size,
                    created_at=f.created_at
                ) for f in files
            ],
            "connection_id": connection_id,
            "count": len(files)
        }

    except Exception as e:
        logger.error(f"Failed to get synced files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get files: {str(e)}")
