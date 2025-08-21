import { useState, useEffect, useRef } from 'preact/hooks';
import { routerService } from '../services/routerService';
import type { Router } from '../types/router';

interface UseRouterHealthOptions {
  checkInterval?: number; // in milliseconds, default 5 minutes
  enabled?: boolean;
}

export function useRouterHealth(routers: Router[], options: UseRouterHealthOptions = {}) {
  const { checkInterval = 300000, enabled = true } = options;
  const [healthStatus, setHealthStatus] = useState<Record<string, 'online' | 'offline' | 'unknown'>>({});
  const [isChecking, setIsChecking] = useState(false);
  const intervalRef = useRef<number | null>(null);
  const syftboxUrlRef = useRef<string | null>(null);

  // Get SyftBox URL once
  useEffect(() => {
    const getSyftboxUrl = async () => {
      try {
        const response = await routerService.getSyftBoxUrl();
        if (response.success && response.data?.url) {
          syftboxUrlRef.current = response.data.url;
        }
      } catch (error) {
        console.error('Failed to get SyftBox URL:', error);
      }
    };
    getSyftboxUrl();
  }, []);

  const checkHealth = async () => {
    if (!enabled || !syftboxUrlRef.current || routers.length === 0) return;

    setIsChecking(true);
    const newHealthStatus: Record<string, 'online' | 'offline' | 'unknown'> = {};

    // Check health for each router
    const healthPromises = routers.map(async (router) => {
      try {
        const response = await routerService.checkRouterHealth(
          router.name,
          router.author,
          syftboxUrlRef.current!
        );
        
        if (response.success && response.data) {
          newHealthStatus[router.name] = response.data.status;
        } else {
          newHealthStatus[router.name] = 'offline';
        }
      } catch (error) {
        console.error(`Health check failed for router ${router.name}:`, error);
        newHealthStatus[router.name] = 'offline';
      }
    });

    await Promise.all(healthPromises);
    setHealthStatus(newHealthStatus);
    setIsChecking(false);
  };

  // Initial health check
  useEffect(() => {
    if (enabled && routers.length > 0) {
      checkHealth();
    }
  }, [enabled, routers.length]);

  // Set up periodic health checks
  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = window.setInterval(checkHealth, checkInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, checkInterval]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const getRouterHealth = (routerName: string): 'online' | 'offline' | 'unknown' => {
    return healthStatus[routerName] || 'unknown';
  };

  const refreshHealth = () => {
    checkHealth();
  };

  return {
    healthStatus,
    isChecking,
    getRouterHealth,
    refreshHealth
  };
}
