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

const API_BASE_URL = '/api';

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
    return this.request<any>('/router/unpublish', {
      method: 'POST',
      body: JSON.stringify({ router_name: routerName }),
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
    return this.request<any>('/router/delete', {
      method: 'POST',
      body: JSON.stringify({ router_name: routerName, published }),
    });
  }

  async getUsername(): Promise<ApiResponse<{ username: string }>> {
    return this.request<{ username: string }>('/username');
  }
}

export const routerService = new RouterService(); 