/**
 * Connection health watchdog hook
 *
 * Periodically checks connection validity and detects issues early.
 * Useful for catching token revocations or API access problems during uploads.
 */
import { useEffect, useState, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';

interface HealthCheckResult {
  healthy: boolean;
  token_valid: boolean;
  can_refresh: boolean;
  user_email?: string;
  last_checked?: string;
  error?: string;
}

interface UseConnectionWatchdogOptions {
  /** Connection ID to monitor */
  connectionId: string | null;
  /** Check interval in milliseconds (default: 5 minutes) */
  intervalMs?: number;
  /** Enable/disable watchdog */
  enabled?: boolean;
  /** Callback when connection becomes unhealthy */
  onUnhealthy?: (error: string) => void;
  /** Callback when connection recovers */
  onHealthy?: () => void;
}

export function useConnectionWatchdog({
  connectionId,
  intervalMs = 5 * 60 * 1000, // 5 minutes default
  enabled = true,
  onUnhealthy,
  onHealthy
}: UseConnectionWatchdogOptions) {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    if (!connectionId || !enabled) return;

    try {
      const response = await fetch(
        `${apiClient.baseURL}/auth/health-check?connection_id=${connectionId}`
      );

      const result: HealthCheckResult = await response.json();

      setLastCheck(new Date());

      // Connection became unhealthy
      if (!result.healthy && isHealthy !== false) {
        setIsHealthy(false);
        setError(result.error || 'Connection health check failed');
        onUnhealthy?.(result.error || 'Connection health check failed');
      }

      // Connection recovered
      if (result.healthy && isHealthy === false) {
        setIsHealthy(true);
        setError(null);
        onHealthy?.();
      }

      // Initial state
      if (isHealthy === null) {
        setIsHealthy(result.healthy);
        if (!result.healthy) {
          setError(result.error || 'Connection is unhealthy');
        }
      }

    } catch (err) {
      console.error('Health check failed:', err);
      setError(err instanceof Error ? err.message : 'Health check request failed');

      if (isHealthy !== false) {
        setIsHealthy(false);
        onUnhealthy?.(err instanceof Error ? err.message : 'Health check request failed');
      }
    }
  }, [connectionId, enabled, isHealthy, onUnhealthy, onHealthy]);

  useEffect(() => {
    if (!connectionId || !enabled) {
      return;
    }

    // Check immediately on mount
    checkHealth();

    // Set up periodic checks
    const intervalId = setInterval(checkHealth, intervalMs);

    return () => clearInterval(intervalId);
  }, [connectionId, enabled, intervalMs, checkHealth]);

  return {
    isHealthy,
    lastCheck,
    error,
    checkNow: checkHealth
  };
}
