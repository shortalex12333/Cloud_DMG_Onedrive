"""Microsoft Graph API client for OneDrive operations"""
from typing import List, Dict, Any, Optional
import requests
import logging

logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """Exception raised for Graph API errors"""
    pass


class GraphClient:
    """Client for Microsoft Graph API OneDrive operations"""

    def __init__(self, access_token: str):
        """
        Initialize Graph API client

        Args:
            access_token: Valid OAuth access token
        """
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Graph API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional requests parameters

        Returns:
            JSON response

        Raises:
            GraphAPIError: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=30,
                **kwargs
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise GraphAPIError(f"Rate limited. Retry after {retry_after} seconds")

            # Handle errors
            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                error_message = error_data.get("error", {}).get("message", "Unknown error")
                raise GraphAPIError(
                    f"Graph API error {response.status_code}: {error_message}"
                )

            return response.json() if response.content else {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise GraphAPIError(f"Request failed: {e}")

    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get authenticated user profile

        Returns:
            User profile data including userPrincipalName, displayName, email
        """
        return self._make_request("GET", "/me")

    def check_onedrive_provisioned(self) -> Dict[str, Any]:
        """
        Check if OneDrive for Business is provisioned for this user

        Returns:
            Drive metadata if provisioned, raises error if not
        """
        try:
            result = self._make_request("GET", "/me/drive")
            return result
        except GraphAPIError as e:
            if "403" in str(e) and "personal site" in str(e).lower():
                raise GraphAPIError(
                    "OneDrive for Business not provisioned. "
                    "Please visit https://office.com, click the OneDrive icon, "
                    "and wait 10-15 minutes for provisioning to complete."
                )
            raise

    def list_root_items(self) -> List[Dict[str, Any]]:
        """
        List items in OneDrive root folder

        Returns:
            List of files and folders
        """
        # Check if OneDrive is provisioned first
        try:
            self.check_onedrive_provisioned()
        except GraphAPIError as e:
            # Re-raise with helpful message
            raise

        result = self._make_request("GET", "/me/drive/root/children")
        return result.get("value", [])

    def list_folder_items(self, folder_path: str) -> List[Dict[str, Any]]:
        """
        List items in a specific folder

        Args:
            folder_path: Path to folder (e.g., "/Documents/Manuals")

        Returns:
            List of files and folders in that path
        """
        # Encode path properly
        encoded_path = folder_path.strip("/")
        endpoint = f"/me/drive/root:/{encoded_path}:/children"

        result = self._make_request("GET", endpoint)
        return result.get("value", [])

    def list_folder_items_by_id(self, folder_id: str) -> List[Dict[str, Any]]:
        """
        List items in a folder by its ID

        Args:
            folder_id: OneDrive folder ID

        Returns:
            List of files and folders
        """
        endpoint = f"/me/drive/items/{folder_id}/children"
        result = self._make_request("GET", endpoint)
        return result.get("value", [])

    def get_item_metadata(self, item_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific item

        Args:
            item_id: OneDrive item ID

        Returns:
            Item metadata
        """
        return self._make_request("GET", f"/me/drive/items/{item_id}")

    def download_file(self, item_id: str) -> bytes:
        """
        Download file content

        Args:
            item_id: OneDrive file ID

        Returns:
            File content as bytes
        """
        endpoint = f"/me/drive/items/{item_id}/content"
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=300  # 5 minutes for large files
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise GraphAPIError(f"Rate limited. Retry after {retry_after} seconds")

            if response.status_code >= 400:
                raise GraphAPIError(f"Download failed with status {response.status_code}")

            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"Download failed: {e}")
            raise GraphAPIError(f"Download failed: {e}")

    def search_files(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for files in OneDrive

        Args:
            query: Search query string

        Returns:
            List of matching files
        """
        endpoint = f"/me/drive/root/search(q='{query}')"
        result = self._make_request("GET", endpoint)
        return result.get("value", [])

    def get_file_thumbnail(self, item_id: str, size: str = "medium") -> Optional[str]:
        """
        Get thumbnail URL for a file

        Args:
            item_id: OneDrive file ID
            size: Thumbnail size (small, medium, large)

        Returns:
            Thumbnail URL or None
        """
        try:
            endpoint = f"/me/drive/items/{item_id}/thumbnails"
            result = self._make_request("GET", endpoint)

            thumbnails = result.get("value", [])
            if thumbnails:
                return thumbnails[0].get(size, {}).get("url")

            return None
        except Exception as e:
            logger.warning(f"Failed to get thumbnail: {e}")
            return None

    def enumerate_all_files(
        self,
        folder_paths: List[str],
        recursive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Enumerate all files in specified folders

        Args:
            folder_paths: List of folder paths to scan
            recursive: If True, scan subfolders recursively

        Returns:
            List of all files found with metadata
        """
        all_files = []

        for folder_path in folder_paths:
            try:
                files = self._enumerate_folder(folder_path, recursive)
                all_files.extend(files)
            except Exception as e:
                logger.error(f"Failed to enumerate {folder_path}: {e}")

        return all_files

    def _enumerate_folder(
        self,
        folder_path: str,
        recursive: bool
    ) -> List[Dict[str, Any]]:
        """
        Enumerate files in a folder (internal recursive method)

        Args:
            folder_path: Folder path
            recursive: If True, scan subfolders

        Returns:
            List of files
        """
        files = []

        try:
            items = self.list_folder_items(folder_path)

            for item in items:
                if "file" in item:
                    # It's a file
                    files.append({
                        "id": item["id"],
                        "name": item["name"],
                        "path": f"{folder_path}/{item['name']}",
                        "size": item.get("size", 0),
                        "mime_type": item.get("file", {}).get("mimeType"),
                        "etag": item.get("eTag"),
                        "created": item.get("createdDateTime"),
                        "modified": item.get("lastModifiedDateTime")
                    })
                elif "folder" in item and recursive:
                    # It's a folder, recurse into it
                    subfolder_path = f"{folder_path}/{item['name']}"
                    subfiles = self._enumerate_folder(subfolder_path, recursive)
                    files.extend(subfiles)

        except Exception as e:
            logger.error(f"Error enumerating {folder_path}: {e}")

        return files


def create_graph_client(access_token: str) -> GraphClient:
    """
    Factory function to create Graph API client

    Args:
        access_token: Valid OAuth access token

    Returns:
        GraphClient instance
    """
    return GraphClient(access_token)
