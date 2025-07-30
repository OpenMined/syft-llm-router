import type { 
  Router, 
  CreateRouterRequest, 
  CreateRouterResponse, 
  PublishRouterRequest,
  RouterDetails,
  RouterList,
  ApiResponse,
  RouterRunStatus
} from '../types/router';

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
}

export const routerService = new RouterService(); 