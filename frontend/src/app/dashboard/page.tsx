/**
 * Main dashboard page after OAuth connection
 */
'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState, Suspense } from 'react';
import { ConnectButton } from '@/components/auth/ConnectButton';
import { FileBrowser } from '@/components/files/FileBrowser';
import { SyncStatusCard } from '@/components/sync/SyncStatusCard';
import { useConnection } from '@/lib/hooks/useConnection';
import { useConnectionWatchdog } from '@/lib/hooks/useConnectionWatchdog';
import { apiClient } from '@/lib/api-client';

function DashboardContent() {
  const searchParams = useSearchParams();
  const [showSuccess, setShowSuccess] = useState(false);
  const [showError, setShowError] = useState<string | null>(null);
  const [showHealthWarning, setShowHealthWarning] = useState(false);
  const [selectedFolders, setSelectedFolders] = useState<string[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Hard-coded yacht ID for demo (in production, this would come from auth)
  const yachtId = 'demo-yacht-001';
  const { status, loading, error } = useConnection(yachtId);

  // Connection health watchdog - checks every 5 minutes
  const { isHealthy, lastCheck, error: healthError } = useConnectionWatchdog({
    connectionId: status?.connection_id || null,
    enabled: status?.connected || false,
    intervalMs: 5 * 60 * 1000, // 5 minutes
    onUnhealthy: (err) => {
      console.warn('Connection became unhealthy:', err);
      setShowHealthWarning(true);
    },
    onHealthy: () => {
      console.log('Connection recovered');
      setShowHealthWarning(false);
    }
  });

  useEffect(() => {
    // Check if just connected
    const connected = searchParams.get('connected');
    const connectionId = searchParams.get('connection_id');

    // Check for OAuth errors (user cancelled, etc.)
    const oauthError = searchParams.get('error');
    const errorDescription = searchParams.get('error_description');

    if (connected === 'true' && connectionId) {
      setShowSuccess(true);
      // Hide success message after 5 seconds
      setTimeout(() => setShowSuccess(false), 5000);
    } else if (oauthError) {
      setShowError(errorDescription || 'Authentication failed');
      // Hide error message after 10 seconds
      setTimeout(() => setShowError(null), 10000);
    }
  }, [searchParams]);

  const handleStartSync = async () => {
    if (!status?.connection_id || selectedFolders.length === 0) {
      alert('Please select folders to sync');
      return;
    }

    try {
      setSyncing(true);
      const job = await apiClient.startSync(status.connection_id, selectedFolders);
      setCurrentJobId(job.job_id);
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to start sync');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">OneDrive Dashboard</h1>
        <p className="text-muted-foreground mb-8">
          Manage your OneDrive connection and document syncing
        </p>

        {showSuccess && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <p className="text-green-800 font-medium">
              Successfully connected to OneDrive!
            </p>
          </div>
        )}

        {showError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 font-medium">
              {showError}
            </p>
          </div>
        )}

        {showHealthWarning && isHealthy === false && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <p className="text-yellow-800 font-medium mb-2">
              ⚠️ Connection Health Warning
            </p>
            <p className="text-yellow-700 text-sm">
              Your OneDrive connection may have issues. {healthError || 'Please reconnect if uploads fail.'}
            </p>
            {lastCheck && (
              <p className="text-yellow-600 text-xs mt-2">
                Last checked: {lastCheck.toLocaleTimeString()}
              </p>
            )}
          </div>
        )}

        <div className="grid gap-6">
          {/* Connection Status Card */}
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Connection Status</h2>

            {loading && <p className="text-muted-foreground">Loading connection status...</p>}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-800 text-sm">
                  Failed to get status: {error}
                </p>
              </div>
            )}

            {!loading && <ConnectButton yachtId={yachtId} />}
          </div>

          {/* File Browser (only show if connected) */}
          {status?.connected && status.connection_id && (
            <div className="border rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Browse OneDrive</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Select folders to sync with CelesteOS
              </p>
              <FileBrowser
                connectionId={status.connection_id}
                onSelectionChange={setSelectedFolders}
              />

              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {selectedFolders.length} folder(s) selected
                </p>
                <button
                  onClick={handleStartSync}
                  disabled={selectedFolders.length === 0 || syncing}
                  className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-2 rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {syncing ? 'Starting...' : 'Start Sync'}
                </button>
              </div>
            </div>
          )}

          {/* Sync Status (only show if there's an active job) */}
          {currentJobId && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Current Sync</h2>
              <SyncStatusCard jobId={currentJobId} />
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="mt-8 border rounded-lg p-6">
          <h3 className="font-semibold mb-2">How It Works</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Connect your OneDrive for Business account</li>
            <li>Browse your OneDrive folders</li>
            <li>Select folders containing yacht documentation</li>
            <li>Click "Start Sync" to begin processing</li>
            <li>Files are automatically categorized and indexed</li>
            <li>Documents become searchable in CelesteOS</li>
          </ol>
        </div>
      </div>
    </main>
  );
}

export default function Dashboard() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background p-8 flex items-center justify-center">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
