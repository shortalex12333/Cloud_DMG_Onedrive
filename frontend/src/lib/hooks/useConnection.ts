/**
 * React hook for managing OneDrive connection state
 */
'use client';

import { useState, useEffect } from 'react';
import { apiClient, ConnectionStatus } from '../api-client';

export function useConnection(yachtId: string) {
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch connection status on mount
  useEffect(() => {
    if (!yachtId) return;

    const fetchStatus = async () => {
      try {
        setLoading(true);
        const connectionStatus = await apiClient.getConnectionStatus(yachtId);
        setStatus(connectionStatus);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
  }, [yachtId]);

  /**
   * Initiate OAuth connection
   */
  const connect = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.connect(yachtId);

      // Redirect to Microsoft OAuth page
      window.location.href = response.auth_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect');
      setLoading(false);
    }
  };

  /**
   * Disconnect OneDrive
   */
  const disconnect = async () => {
    if (!status?.connection_id) {
      setError('No connection to disconnect');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      await apiClient.disconnect(status.connection_id);

      // SECURITY: Clear ALL browser cache to prevent any stale data
      // Clear localStorage
      if (typeof window !== 'undefined') {
        try {
          // Clear any cached connection data
          localStorage.removeItem('onedrive_connection');
          localStorage.removeItem('connection_id');
          // Clear sessionStorage too
          sessionStorage.clear();
        } catch (e) {
          console.warn('Failed to clear browser storage:', e);
        }
      }

      // SECURITY: Fully clear status to prevent stale connection_id usage
      setStatus(null);

      // Immediately refresh to ensure we get the correct state
      setTimeout(() => {
        refresh();
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Refresh connection status
   */
  const refresh = async () => {
    try {
      setLoading(true);
      const connectionStatus = await apiClient.getConnectionStatus(yachtId);
      setStatus(connectionStatus);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh status');
    } finally {
      setLoading(false);
    }
  };

  return {
    status,
    loading,
    error,
    connect,
    disconnect,
    refresh,
  };
}
