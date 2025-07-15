import type { ApiResponse } from '../types/router';

const SYFTBOX_BASE_URL = 'https://dev.syftbox.net';

interface SearchResult {
  content: string;
  id: string;
  metadata: {
    filename: string;
  };
  score: number;
}

interface SearchResponse {
  request_id: string;
  data: {
    message: {
      body: {
        results: SearchResult[];
      };
    };
    poll_url?: string;
  };
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatRequest {
  model: string;
  messages: ChatMessage[];
}

interface ChatResponse {
  request_id: string;
  data: {
    message: {
      body: {
        message: {
          content: string;
        };
      };
    };
    poll_url?: string;
  };
}

interface PollResponse {
  request_id: string;
  data: {
    poll_url?: string;
  };
  message?: string;
}

class ChatService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${SYFTBOX_BASE_URL}${endpoint}`, {
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

  private async pollForResponse<T>(pollUrl: string, maxAttempts: number = 20): Promise<ApiResponse<T>> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const response = await fetch(`${SYFTBOX_BASE_URL}${pollUrl}`);
        const data = await response.json();

        // Check if the response has a status_code of 200 (resolved response)
        if (response.status === 200 && data?.data?.message?.status_code === 200) {
          return {
            success: true,
            data,
          };
        } else if (response.status === 202 || (data?.data?.message?.status_code !== 200)) {
          // Still processing, wait and try again
          await new Promise(resolve => setTimeout(resolve, 2000));
          continue;
        } else {
          return {
            success: false,
            error: data.message || `HTTP ${response.status}: ${response.statusText}`,
          };
        }
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error occurred',
        };
      }
    }

    return {
      success: false,
      error: 'Request timed out after maximum attempts',
    };
  }

  async search(routerName: string, author: string, query: string): Promise<ApiResponse<SearchResponse>> {
    const encodedQuery = encodeURIComponent(query);
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/search?query="${encodedQuery}"`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);
    
    const endpoint = `/api/v1/send/msg?x-syft-url=${encodedSyftUrl}&x-syft-from=syft@guest.org`;
    
    const response = await this.request<SearchResponse>(endpoint, {
      method: 'POST',
    });

    // If we get a 202, poll for the response
    if (response.success && response.data?.data?.poll_url) {
      return this.pollForResponse<SearchResponse>(response.data.data.poll_url);
    }

    return response;
  }

  async chat(routerName: string, author: string, messages: ChatMessage[]): Promise<ApiResponse<ChatResponse>> {
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/chat`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);
    
    const endpoint = `/api/v1/send/msg?x-syft-url=${encodedSyftUrl}&x-syft-from=syft@guest.org`;
    
    const payload: ChatRequest = {
      model: "tinyllama:latest",
      messages,
    };

    const response = await this.request<ChatResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // If we get a 202, poll for the response
    if (response.success && response.data?.data?.poll_url) {
      return this.pollForResponse<ChatResponse>(response.data.data.poll_url);
    }

    return response;
  }

  async getAvailableRouters(): Promise<ApiResponse<Array<{ name: string; author: string; services: string[] }>>> {
    // This would typically come from your router list API
    // For now, we'll return a mock response
    return {
      success: true,
      data: [
        { name: 'mit', author: 'alice@openmined.org', services: ['search'] },
        { name: 'oreilly', author: 'alice@openmined.org', services: ['chat'] },
      ],
    };
  }
}

export const chatService = new ChatService();
export type { SearchResult, ChatMessage, SearchResponse, ChatResponse }; 