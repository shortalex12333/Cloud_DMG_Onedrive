/**
 * OneDrive connection button component
 */
'use client';

import { useConnection } from '@/lib/hooks/useConnection';

interface ConnectButtonProps {
  yachtId: string;
}

export function ConnectButton({ yachtId }: ConnectButtonProps) {
  const { status, loading, error, connect, disconnect } = useConnection(yachtId);

  if (loading) {
    return (
      <button
        disabled
        className="bg-gray-400 text-white px-6 py-3 rounded-md font-medium cursor-not-allowed"
      >
        Loading...
      </button>
    );
  }

  if (status?.connected) {
    return (
      <div className="space-y-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-green-800 font-medium">Connected</p>
          <p className="text-green-600 text-sm mt-1">
            {status.user_principal_name}
          </p>
        </div>

        <button
          onClick={disconnect}
          className="bg-red-600 text-white hover:bg-red-700 px-6 py-3 rounded-md font-medium w-full"
        >
          Disconnect OneDrive
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button
        onClick={connect}
        disabled={loading}
        className="bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-3 rounded-md font-medium w-full disabled:opacity-50"
      >
        Connect OneDrive
      </button>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}
    </div>
  );
}
