"""
Sync manager for OneDrive to Supabase document syncing
Handles file enumeration, download, upload, and processing
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import hashlib
import requests
from sqlalchemy.orm import Session
from supabase import create_client

from app.config import settings
from app.core.graph_client import create_graph_client, GraphAPIError
from app.core.metadata_extractor import extract_metadata_from_onedrive_path, format_for_digest_service
from app.models.connection import OneDriveConnection
from app.models.sync_state import OneDriveSyncState
from app.models.sync_job import OneDriveSyncJob

logger = logging.getLogger(__name__)


class SyncManager:
    """Manages syncing files from OneDrive to Supabase and processing"""

    def __init__(self, db: Session):
        """
        Initialize sync manager

        Args:
            db: Database session
        """
        self.db = db
        self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)

    def create_sync_job(
        self,
        connection_id: str,
        yacht_id: str,
        folder_paths: List[str]
    ) -> OneDriveSyncJob:
        """
        Create a new sync job

        Args:
            connection_id: OneDrive connection ID
            yacht_id: Yacht identifier
            folder_paths: List of folder paths to sync

        Returns:
            Created sync job
        """
        job = OneDriveSyncJob(
            connection_id=connection_id,
            yacht_id=yacht_id,
            job_status='pending'
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        logger.info(f"Created sync job {job.id} for connection {connection_id}")
        return job

    def enumerate_files_for_sync(
        self,
        access_token: str,
        folder_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Enumerate all files in selected folders

        Args:
            access_token: Valid OAuth access token
            folder_paths: List of folder paths to scan

        Returns:
            List of file metadata dictionaries
        """
        graph_client = create_graph_client(access_token)

        try:
            all_files = graph_client.enumerate_all_files(folder_paths, recursive=True)
            logger.info(f"Enumerated {len(all_files)} files from {len(folder_paths)} folders")
            return all_files
        except GraphAPIError as e:
            logger.error(f"Failed to enumerate files: {e}")
            raise

    def sync_file(
        self,
        access_token: str,
        connection_id: str,
        yacht_id: str,
        file_info: Dict[str, Any],
        job_id: str
    ) -> bool:
        """
        Sync a single file from OneDrive to Supabase and process

        Args:
            access_token: Valid OAuth access token
            connection_id: OneDrive connection ID
            yacht_id: Yacht identifier
            file_info: File metadata from Graph API
            job_id: Sync job ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already synced (by OneDrive item ID)
            existing = self.db.query(OneDriveSyncState).filter(
                OneDriveSyncState.connection_id == connection_id,
                OneDriveSyncState.onedrive_item_id == file_info['id'],
                OneDriveSyncState.sync_status == 'completed'
            ).first()

            if existing and existing.onedrive_etag == file_info.get('etag'):
                logger.info(f"File {file_info['name']} already synced and unchanged, skipping")
                return True

            # Create or update sync state
            sync_state = existing or OneDriveSyncState(
                connection_id=connection_id,
                yacht_id=yacht_id,
                onedrive_item_id=file_info['id']
            )

            sync_state.onedrive_path = file_info['path']
            sync_state.file_name = file_info['name']
            sync_state.file_size = file_info.get('size', 0)
            sync_state.onedrive_etag = file_info.get('etag')
            sync_state.sync_status = 'syncing'

            if not existing:
                self.db.add(sync_state)

            self.db.commit()
            self.db.refresh(sync_state)

            # Download file from OneDrive
            graph_client = create_graph_client(access_token)
            file_content = graph_client.download_file(file_info['id'])

            logger.info(f"Downloaded {file_info['name']} ({len(file_content)} bytes)")

            # Extract metadata from path
            metadata = extract_metadata_from_onedrive_path(file_info['path'])
            sync_state.extracted_metadata = metadata
            self.db.commit()

            # Upload to Supabase Storage
            storage_path = f"{yacht_id}/{metadata['system_path']}/{file_info['name']}"
            try:
                self.supabase.storage.from_('yacht-documents').upload(
                    path=storage_path,
                    file=file_content,
                    file_options={"content-type": file_info.get('mime_type', 'application/octet-stream')}
                )
                logger.info(f"Uploaded to Supabase: {storage_path}")
            except Exception as e:
                # File might already exist, try update
                logger.warning(f"Upload failed, trying update: {e}")
                self.supabase.storage.from_('yacht-documents').update(
                    path=storage_path,
                    file=file_content,
                    file_options={"content-type": file_info.get('mime_type', 'application/octet-stream')}
                )

            # Send to digest service for processing
            self._send_to_digest_service(
                file_content=file_content,
                filename=file_info['name'],
                onedrive_path=file_info['path'],
                yacht_id=yacht_id
            )

            # Update sync state to completed
            sync_state.sync_status = 'completed'
            self.db.commit()

            logger.info(f"Successfully synced {file_info['name']}")
            return True

        except Exception as e:
            logger.error(f"Failed to sync {file_info.get('name', 'unknown')}: {e}")

            # Update sync state to failed
            if sync_state:
                sync_state.sync_status = 'failed'
                self.db.commit()

            return False

    def _send_to_digest_service(
        self,
        file_content: bytes,
        filename: str,
        onedrive_path: str,
        yacht_id: str
    ):
        """
        Send file to document digest service for processing

        Args:
            file_content: File bytes
            filename: File name
            onedrive_path: OneDrive path
            yacht_id: Yacht identifier
        """
        # Generate yacht signature (same as NAS system)
        signature = hashlib.sha256(f"{yacht_id}{settings.yacht_salt}".encode()).hexdigest()

        # Format metadata
        data_payload = format_for_digest_service(onedrive_path, filename, yacht_id)

        # Prepare request
        endpoint = f"{settings.digest_service_url}/webhook/ingest-docs-nas-cloud"

        files = {
            'file': (filename, file_content, 'application/octet-stream')
        }

        headers = {
            'X-Yacht-ID': yacht_id,
            'X-Yacht-Signature': signature
        }

        import json
        data = {
            'data': json.dumps(data_payload)
        }

        # Send request
        response = requests.post(
            endpoint,
            files=files,
            data=data,
            headers=headers,
            timeout=120
        )

        if response.status_code != 200:
            logger.error(f"Digest service returned {response.status_code}: {response.text}")
            raise Exception(f"Digest service failed: {response.status_code}")

        logger.info(f"Sent {filename} to digest service successfully")

    def update_job_progress(
        self,
        job_id: str,
        files_succeeded: int,
        files_failed: int
    ):
        """
        Update sync job progress

        Args:
            job_id: Sync job ID
            files_succeeded: Count of successful syncs
            files_failed: Count of failed syncs
        """
        job = self.db.query(OneDriveSyncJob).filter(
            OneDriveSyncJob.id == job_id
        ).first()

        if job:
            job.files_succeeded = files_succeeded
            job.files_failed = files_failed
            self.db.commit()

    def complete_job(
        self,
        job_id: str,
        status: str = 'completed'
    ):
        """
        Mark sync job as completed

        Args:
            job_id: Sync job ID
            status: Final status (completed or failed)
        """
        job = self.db.query(OneDriveSyncJob).filter(
            OneDriveSyncJob.id == job_id
        ).first()

        if job:
            job.job_status = status
            job.completed_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Sync job {job_id} {status}")
