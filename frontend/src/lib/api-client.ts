/**
 * API client for backend communication
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ConnectResponse {
  auth_url: string;
  state: string;
}

export interface ConnectionStatus {
  connected: boolean;
  user_principal_name?: string;
  connection_id?: string;
  sync_enabled?: boolean;
}

export interface FileItem {
  id: string;
  name: string;
  path: string;
  is_folder: boolean;
  size?: number;
  mime_type?: string;
  created?: string;
  modified?: string;
}

export interface FileListResponse {
  items: FileItem[];
  path: string;
}

export interface SyncJobStatus {
  job_id: string;
  job_status: string;
  total_files_found: number;
  files_succeeded: number;
  files_failed: number;
  started_at?: string;
  completed_at?: string;
}

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Auth endpoints
   */
  async connect(yachtId: string): Promise<ConnectResponse> {
    const response = await fetch(`${this.baseURL}/api/v1/auth/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ yacht_id: yachtId }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to initiate connection');
    }

    return response.json();
  }

  async getConnectionStatus(yachtId: string): Promise<ConnectionStatus> {
    const response = await fetch(
      `${this.baseURL}/api/v1/auth/status?yacht_id=${yachtId}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get connection status');
    }

    return response.json();
  }

  async disconnect(connectionId: string): Promise<void> {
    const response = await fetch(
      `${this.baseURL}/api/v1/auth/disconnect?connection_id=${connectionId}`,
      {
        method: 'POST',
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to disconnect');
    }
  }

  /**
   * File browsing endpoints
   */
  async browseFiles(
    connectionId: string,
    path: string = '/'
  ): Promise<FileListResponse> {
    const response = await fetch(
      `${this.baseURL}/api/v1/files/browse?connection_id=${connectionId}&path=${encodeURIComponent(
        path
      )}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to browse files');
    }

    return response.json();
  }

  /**
   * Sync endpoints
   */
  async startSync(
    connectionId: string,
    folderPaths: string[]
  ): Promise<SyncJobStatus> {
    const response = await fetch(`${this.baseURL}/api/v1/sync/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        connection_id: connectionId,
        folder_paths: folderPaths,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to start sync');
    }

    return response.json();
  }

  async getSyncStatus(jobId: string): Promise<SyncJobStatus> {
    const response = await fetch(
      `${this.baseURL}/api/v1/sync/status?job_id=${jobId}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get sync status');
    }

    return response.json();
  }

  async getSyncHistory(connectionId: string, limit: number = 10): Promise<any> {
    const response = await fetch(
      `${this.baseURL}/api/v1/sync/history?connection_id=${connectionId}&limit=${limit}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get sync history');
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseURL}/health`);
    return response.json();
  }
}

export const apiClient = new APIClient();
