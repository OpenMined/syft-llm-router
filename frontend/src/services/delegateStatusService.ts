import { routerService } from './routerService';
import type { DelegateStatus } from '../types/router';

class DelegateStatusService {
  private status: DelegateStatus | null = null;
  private isLoaded = false;
  private isLoading = false;
  private listeners: Set<(status: DelegateStatus | null) => void> = new Set();

  // Subscribe to status changes
  subscribe(callback: (status: DelegateStatus | null) => void) {
    this.listeners.add(callback);
    
    // Immediately call with current status if available
    if (this.isLoaded) {
      callback(this.status);
    } else if (!this.isLoading) {
      // Load status if not already loaded/loading
      this.loadStatus();
    }

    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  // Get current status (synchronous)
  getCurrentStatus(): DelegateStatus | null {
    return this.status;
  }

  // Check if status is loaded
  isStatusLoaded(): boolean {
    return this.isLoaded;
  }

  // Load status from API
  private async loadStatus() {
    if (this.isLoading) return;
    
    this.isLoading = true;
    
    try {
      const response = await routerService.getGatekeeperStatus();
      if (response.success && response.data) {
        this.status = response.data;
      } else {
        this.status = null;
      }
    } catch (error) {
      console.warn('Failed to load delegate status:', error);
      this.status = null;
    } finally {
      this.isLoaded = true;
      this.isLoading = false;
      
      // Notify all listeners
      this.notifyListeners();
    }
  }

  // Refresh status (used after opt-in)
  async refreshStatus(): Promise<DelegateStatus | null> {
    this.isLoading = true;
    
    try {
      const response = await routerService.getGatekeeperStatus();
      if (response.success && response.data) {
        this.status = response.data;
      } else {
        this.status = null;
      }
    } catch (error) {
      console.warn('Failed to refresh delegate status:', error);
      this.status = null;
    } finally {
      this.isLoading = false;
      this.notifyListeners();
    }
    
    return this.status;
  }

  // Opt in as delegate and refresh status
  async optIn(): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await routerService.optInAsGatekeeper();
      if (response.success) {
        // Refresh status after successful opt-in
        await this.refreshStatus();
        return { success: true };
      } else {
        return { success: false, error: response.error };
      }
    } catch (error) {
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Clear cache (useful for logout or user change)
  clearCache() {
    this.status = null;
    this.isLoaded = false;
    this.isLoading = false;
    this.notifyListeners();
  }

  private notifyListeners() {
    this.listeners.forEach(callback => callback(this.status));
  }
}

// Export singleton instance
export const delegateStatusService = new DelegateStatusService();