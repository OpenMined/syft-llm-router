import type { 
  Router, 
  CreateRouterRequest, 
  CreateRouterResponse, 
  PublishRouterRequest,
  RouterDetails,
  RouterList,
  ApiResponse,
  RouterRunStatus,
  AvailableDelegatesResponse,
  DelegateRouterRequest,
  DelegateRouterResponse,
  RevokeDelegationRequest,
  RevokeDelegationResponse,
  DelegateControlRequest,
  DelegateControlResponse,
  DCALogsResponse,
  DelegateStatus
} from '../types/router';
import { GATEKEEPER_API } from '../utils/constants';

const API_BASE_URL = '';

interface TransactionHistory {
  transactions: Transaction[];
  total_credits: number;
  total_debits: number;
}

interface PaginationInfo {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface TransactionSummary {
  completed_count: number;
  pending_count: number;
  total_spent: number;
}

interface PaginatedTransactionHistory {
  data: TransactionHistory;
  pagination: PaginationInfo;
  summary: TransactionSummary;
}

// Analytics interfaces
interface DailyMetrics {
  date: string;
  query_count: number;
  total_earned: number;
  total_spent: number;
  net_profit: number;
  completed_count: number;
  pending_count: number;
}

interface AnalyticsSummary {
  total_days: number;
  avg_daily_queries: number;
  avg_daily_earned: number;
  avg_daily_spent: number;
  avg_daily_profit: number;
  total_queries: number;
  total_earned: number;
  total_spent: number;
  total_profit: number;
  success_rate: number;
}

interface AnalyticsResponse {
  daily_metrics: DailyMetrics[];
  summary: AnalyticsSummary;
}

interface Transaction {
  id: string;
  sender_email: string;
  recipient_email: string;
  amount: number;
  service_type: string;
  router_name?: string;
  status: 'completed' | 'pending' | 'failed';
  created_at: string;
  updated_at: string;
}

class RouterService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const data = await response.json();

      // Check if this is a polling response (async request)
      if (data.data && data.data.poll_url) {
        return {
          success: true,
          data: {
            ...data,
            isAsync: true,
            message: data.message || 'Request has been accepted. Please check back later.'
          },
        };
      }

      if (!response.ok) {
        return {
          success: false,
          error: data.message || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }

  async listRouters(): Promise<ApiResponse<Router[]>> {
    const response = await this.request<RouterList>('/router/list');
    if (response.success && response.data) {
      return {
        success: true,
        data: response.data.routers,
      };
    }
    return {
      success: false,
      error: response.error || 'Failed to fetch routers',
    };
  }

  async createRouter(request: CreateRouterRequest): Promise<ApiResponse<CreateRouterResponse>> {
    return this.request<CreateRouterResponse>('/router/create', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async routerExists(name: string): Promise<ApiResponse<boolean>> {
    return this.request<boolean>(`/router/exists?name=${encodeURIComponent(name)}`);
  }

  async publishRouter(request: PublishRouterRequest): Promise<ApiResponse<any>> {
    return this.request<any>('/router/publish', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async unpublishRouter(routerName: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/router/unpublish?router_name=${encodeURIComponent(routerName)}`, {
      method: 'PUT',
    });
  }

  async getRouterDetails(routerName: string, author: string, published: boolean): Promise<ApiResponse<RouterDetails>> {
    const params = new URLSearchParams({ 
      router_name: routerName, 
      author: author,
      published: String(published) 
    });
    return this.request<RouterDetails>(`/router/details?${params.toString()}`);
  }

  async getRouterStatus(routerName: string): Promise<ApiResponse<RouterRunStatus>> {
    const params = new URLSearchParams({ 
      router_name: routerName
    });
    return this.request<RouterRunStatus>(`/router/status?${params.toString()}`);
  }

  async deleteRouter(routerName: string, published: boolean): Promise<ApiResponse<any>> {
    const params = new URLSearchParams({ 
      router_name: routerName, 
      published: String(published) 
    });
    return this.request<any>(`/router/delete?${params.toString()}`, {
      method: 'DELETE',
    });
  }

  async getUsername(): Promise<ApiResponse<{ username: string }>> {
    return this.request<{ username: string }>('/username');
  }

  async getSyftBoxUrl(): Promise<ApiResponse<{ url: string }>> {
    return this.request<{ url: string }>('/sburl');
  }

  async getAccountInfo(): Promise<ApiResponse<{ id: string; email: string; balance: number }>> {
    return this.request<{ id: string; email: string; balance: number }>(
      '/account/info'
    );
  }

    async getTransactionHistory(
    page: number = 1, 
    pageSize: number = 10,
    status?: string,
    startDate?: string,
    endDate?: string
  ): Promise<ApiResponse<PaginatedTransactionHistory>> {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });

    if (status && status !== 'all') {
      params.append('status', status);
    }

    if (startDate) {
      params.append('start_date', startDate);
    }

    if (endDate) {
      params.append('end_date', endDate);
    }

    return this.request<PaginatedTransactionHistory>(`/account/history?${params.toString()}`);
  }

  async getAnalytics(
    startDate?: string,
    endDate?: string
  ): Promise<ApiResponse<AnalyticsResponse>> {
    const params = new URLSearchParams();

    if (startDate) {
      params.append('start_date', startDate);
    }

    if (endDate) {
      params.append('end_date', endDate);
    }

    return this.request<AnalyticsResponse>(`/account/analytics?${params.toString()}`);
  }

  // Gatekeeper/Delegation Methods
  async optInAsGatekeeper(): Promise<ApiResponse<{ success: boolean }>> {
    return this.request<{ success: boolean }>(GATEKEEPER_API.OPT_IN, {
      method: 'POST',
    });
  }

  async getGatekeeperStatus(): Promise<ApiResponse<DelegateStatus>> {
    return this.request<DelegateStatus>(GATEKEEPER_API.STATUS);
  }

  async listGatekeepers(): Promise<ApiResponse<AvailableDelegatesResponse>> {
    return this.request<AvailableDelegatesResponse>(GATEKEEPER_API.LIST);
  }

  async grantGatekeeper(request: DelegateRouterRequest): Promise<ApiResponse<DelegateRouterResponse>> {
    return this.request<DelegateRouterResponse>(GATEKEEPER_API.GRANT, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async revokeGatekeeper(request: RevokeDelegationRequest): Promise<ApiResponse<RevokeDelegationResponse>> {
    return this.request<RevokeDelegationResponse>(GATEKEEPER_API.REVOKE, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getGatekeeperLogs(routerName: string): Promise<ApiResponse<DCALogsResponse>> {
    return this.request<DCALogsResponse>(`${GATEKEEPER_API.LOGS}?router_name=${encodeURIComponent(routerName)}`);
  }

  async getGatekeeperAccessToken(routerName: string, routerAuthor: string): Promise<ApiResponse<{ access_token: string }>> {
    const params = new URLSearchParams({
      router_name: routerName,
      router_author: routerAuthor
    });
    return this.request<{ access_token: string }>(`${GATEKEEPER_API.ACCESS_TOKEN}?${params.toString()}`);
  }

  async checkRouterHealth(routerName: string, routerAuthor: string, syftboxUrl: string): Promise<ApiResponse<{ status: 'online' | 'offline' }>> {
    try {
      const healthUrl = `${syftboxUrl}api/v1/send/msg?timeout=5000&x-syft-from=guest@syft.org&x-syft-url=${encodeURIComponent(`syft://${routerAuthor}/app_data/${routerName}/rpc/health`)}`;
      
      const response = await fetch(healthUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Consider 200 status and response.data.status_code === 200 as online, anything else as offline
      const data = await response.json();
      const status = response.status === 200 && data.data.message.status_code === 200 ? 'online' : 'offline';
      
      return {
        success: true,
        data: { status }
      };
    } catch (error) {
      return {
        success: true,
        data: { status: 'offline' }
      };
    }
  }

  async updateGatekeeperControl(
    syftboxUrl: string,
    authorEmail: string,
    routerName: string,
    services: any[]
  ): Promise<ApiResponse<DelegateControlResponse>> {
    // First get the current user's email
    const accountResponse = await this.getAccountInfo();
    if (!accountResponse.success || !accountResponse.data) {
      return {
        success: false,
        error: 'Failed to get current user info',
      };
    }
    const currentUserEmail = accountResponse.data.email;

    // Then get the access token
    const tokenResponse = await this.getGatekeeperAccessToken(routerName, authorEmail);
    if (!tokenResponse.success || !tokenResponse.data) {
      return {
        success: false,
        error: 'Failed to get access token',
      };
    }

    const request: DelegateControlRequest = {
      router_name: routerName,
      delegate_email: currentUserEmail, // Set to current user's email
      control_type: 'update_pricing',
      control_data: {
        pricing_updates: services.map(service => ({
          service_type: service.type,
          new_pricing: service.pricing,
          new_charge_type: service.charge_type
        }))
      },
      delegate_access_token: tokenResponse.data.access_token
    };

    // Special handling for delegate control through cache server
    const syftUrl = `syft://${authorEmail}/app_data/SyftRouter/rpc${GATEKEEPER_API.CONTROL}`;
    // Fix double slash issue by ensuring proper URL concatenation
    const baseUrl = syftboxUrl.endsWith('/') ? syftboxUrl.slice(0, -1) : syftboxUrl;
    const cacheUrl = `${baseUrl}/api/v1/send/msg?x-syft-url=${encodeURIComponent(syftUrl)}&x-syft-from=guest@syft.org`;
    
    try {
      const response = await fetch(cacheUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      const data = await response.json();
      
      // Check if this is a polling response (async request) - also check for 202 status
      if ((data.data && data.data.poll_url) || response.status === 202) {
        console.log('Detected async response (poll_url or 202 status)');
        return {
          success: true,
          data: {
            ...data,
            isAsync: true,
            message: data.message || 'Request has been accepted. Please check back later.'
          },
        };
      }

      if (!response.ok) {
        return {
          success: false,
          error: data.message || `HTTP ${response.status}: ${response.statusText}`,
        };
      }

      return {
        success: true,
        data,
      };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };
    }
  }
}

export const routerService = new RouterService(); 