import type { ApiResponse } from '../types/router';

export interface UserAccount {
  email: string;
  balance: number;
  password: string;
  organization?: string;
}

export interface UserAccountView {
  email: string;
  balance: number;
  organization?: string;
}

export interface CreateAccountRequest {
  email: string;
  organization?: string;
  password?: string;
}

export interface UpdateCredentialsRequest {
  email: string;
  organization?: string;
  password?: string;
}

const API_BASE_URL = '';

class AccountingService {
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
          error: data.detail || data.message || `HTTP ${response.status}: ${response.statusText}`,
          statusCode: response.status,
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

  async getAccountInfo(): Promise<ApiResponse<UserAccountView>> {
    return this.request<UserAccountView>('/account/info');
  }

  async createAccount(request: CreateAccountRequest): Promise<ApiResponse<UserAccount>> {
    const params = new URLSearchParams({
      email: request.email,
    });

    if (request.organization) {
      params.append('organization', request.organization);
    }

    if (request.password) {
      params.append('password', request.password);
    }

    return this.request<UserAccount>(`/account/credential/create?${params.toString()}`, {
      method: 'POST',
    });
  }

  async updateCredentials(request: UpdateCredentialsRequest): Promise<ApiResponse<UserAccount>> {
    const params = new URLSearchParams({
      email: request.email,
    });

    if (request.organization) {
      params.append('organization', request.organization);
    }

    if (request.password) {
      params.append('password', request.password);
    }

    return this.request<UserAccount>(`/account/credential/update?${params.toString()}`, {
      method: 'POST',
    });
  }

  async getAccountingUrl(): Promise<ApiResponse<string>> {
    return this.request<string>('/account/url');
  }

  async getUsername(): Promise<ApiResponse<{ username: string }>> {
    return this.request<{ username: string }>('/username');
  }
}

export const accountingService = new AccountingService(); 