/**
 * Sync status display component
 */
'use client';

import { useState, useEffect } from 'react';
import { apiClient, SyncJobStatus } from '@/lib/api-client';

interface SyncStatusCardProps {
  jobId: string;
  autoRefresh?: boolean;
}

export function SyncStatusCard({ jobId, autoRefresh = true }: SyncStatusCardProps) {
  const [status, setStatus] = useState<SyncJobStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStatus();

    if (autoRefresh) {
      const interval = setInterval(loadStatus, 3000); // Poll every 3 seconds
      return () => clearInterval(interval);
    }
  }, [jobId, autoRefresh]);

  const loadStatus = async () => {
    try {
      setError(null);
      const jobStatus = await apiClient.getSyncStatus(jobId);
      setStatus(jobStatus);
      setLoading(false);

      // Stop auto-refresh if job is complete
      if (jobStatus.job_status === 'completed' || jobStatus.job_status === 'failed') {
        // Could stop interval here
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load status');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-6">
        <p className="text-muted-foreground">Loading status...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-red-50">
        <p className="text-red-800 text-sm">{error}</p>
      </div>
    );
  }

  if (!status) return null;

  const progress =
    status.total_files_found > 0
      ? ((status.files_succeeded + status.files_failed) / status.total_files_found) * 100
      : 0;

  const statusColor = {
    pending: 'text-gray-600',
    running: 'text-blue-600',
    completed: 'text-green-600',
    failed: 'text-red-600',
  }[status.job_status] || 'text-gray-600';

  return (
    <div className="border rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Sync Job Status</h3>
        <span className={`text-sm font-medium ${statusColor}`}>
          {status.job_status.toUpperCase()}
        </span>
      </div>

      {/* Progress bar */}
      {status.total_files_found > 0 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-muted-foreground mb-1">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <div className="text-2xl font-bold">{status.total_files_found}</div>
          <div className="text-xs text-muted-foreground">Total Files</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-600">
            {status.files_succeeded}
          </div>
          <div className="text-xs text-muted-foreground">Succeeded</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-600">
            {status.files_failed}
          </div>
          <div className="text-xs text-muted-foreground">Failed</div>
        </div>
      </div>

      {/* Timestamps */}
      {status.started_at && (
        <div className="mt-4 pt-4 border-t text-xs text-muted-foreground space-y-1">
          <div>Started: {new Date(status.started_at).toLocaleString()}</div>
          {status.completed_at && (
            <div>Completed: {new Date(status.completed_at).toLocaleString()}</div>
          )}
        </div>
      )}
    </div>
  );
}
