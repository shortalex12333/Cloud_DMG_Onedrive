/**
 * Main dashboard page after OAuth connection
 */
'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ConnectButton } from '@/components/auth/ConnectButton';

export default function Dashboard() {
  const searchParams = useSearchParams();
  const [showSuccess, setShowSuccess] = useState(false);

  // Hard-coded yacht ID for demo (in production, this would come from auth)
  const yachtId = 'demo-yacht-001';

  useEffect(() => {
    // Check if just connected
    const connected = searchParams.get('connected');
    const connectionId = searchParams.get('connection_id');

    if (connected === 'true' && connectionId) {
      setShowSuccess(true);
      // Hide success message after 5 seconds
      setTimeout(() => setShowSuccess(false), 5000);
    }
  }, [searchParams]);

  return (
    <main className="min-h-screen bg-background p-8">
      <div className="max-w-4xl mx-auto">
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

        <div className="grid gap-6">
          {/* Connection Status Card */}
          <div className="border rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4">Connection Status</h2>
            <ConnectButton yachtId={yachtId} />
          </div>

          {/* Coming Soon Cards */}
          <div className="border rounded-lg p-6 bg-muted/50">
            <h2 className="text-xl font-semibold mb-4">File Browser</h2>
            <p className="text-muted-foreground">
              Week 3: Browse and select OneDrive folders to sync
            </p>
          </div>

          <div className="border rounded-lg p-6 bg-muted/50">
            <h2 className="text-xl font-semibold mb-4">Sync Status</h2>
            <p className="text-muted-foreground">
              Week 3: View real-time sync progress and history
            </p>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 border rounded-lg p-6">
          <h3 className="font-semibold mb-2">Next Steps</h3>
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Click "Connect OneDrive" to authorize access</li>
            <li>Sign in with your Microsoft 365 account</li>
            <li>Grant permissions to CelesteOS</li>
            <li>Browse and select folders to sync (Week 3)</li>
            <li>Monitor sync progress (Week 3)</li>
          </ol>
        </div>
      </div>
    </main>
  );
}
