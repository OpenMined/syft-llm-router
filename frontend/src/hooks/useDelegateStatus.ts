import { useState, useEffect } from 'preact/hooks';
import { delegateStatusService } from '../services/delegateStatusService';
import type { DelegateStatus } from '../types/router';

export function useDelegateStatus() {
  const [status, setStatus] = useState<DelegateStatus | null>(
    delegateStatusService.getCurrentStatus()
  );
  const [isLoaded, setIsLoaded] = useState(
    delegateStatusService.isStatusLoaded()
  );

  useEffect(() => {
    // Subscribe to status changes
    const unsubscribe = delegateStatusService.subscribe((newStatus) => {
      setStatus(newStatus);
      setIsLoaded(delegateStatusService.isStatusLoaded());
    });

    return unsubscribe;
  }, []);

  const optIn = async () => {
    return await delegateStatusService.optIn();
  };

  const refresh = async () => {
    return await delegateStatusService.refreshStatus();
  };

  const clearCache = () => {
    delegateStatusService.clearCache();
  };

  return {
    status,
    isLoaded,
    optIn,
    refresh,
    clearCache
  };
}