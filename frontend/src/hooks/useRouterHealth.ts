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
  const [checkingRouters, setCheckingRouters] = useState<Set<string>>(new Set());
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
    
    // Mark all routers as being checked
    setCheckingRouters(new Set(routers.map(r => r.name)));

    // Check health for each router individually and update status as soon as each completes
    const healthPromises = routers.map(async (router) => {
      try {
        const response = await routerService.checkRouterHealth(
          router.name,
          router.author,
          syftboxUrlRef.current!
        );
        
        // Update status immediately for this router
        setHealthStatus(prev => ({
          ...prev,
          [router.name]: response.success && response.data ? response.data.status : 'offline'
        }));
        
        // Remove this router from checking set
        setCheckingRouters(prev => {
          const newSet = new Set(prev);
          newSet.delete(router.name);
          return newSet;
        });
      } catch (error) {
        console.error(`Health check failed for router ${router.name}:`, error);
        // Update status immediately for this router
        setHealthStatus(prev => ({
          ...prev,
          [router.name]: 'offline'
        }));
        
        // Remove this router from checking set
        setCheckingRouters(prev => {
          const newSet = new Set(prev);
          newSet.delete(router.name);
          return newSet;
        });
      }
    });

    // Wait for all health checks to complete before setting isChecking to false
    await Promise.all(healthPromises);
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

  const isRouterChecking = (routerName: string): boolean => {
    return checkingRouters.has(routerName);
  };

  const refreshHealth = () => {
    checkHealth();
  };

  return {
    healthStatus,
    isChecking,
    checkingRouters,
    getRouterHealth,
    isRouterChecking,
    refreshHealth
  };
}
