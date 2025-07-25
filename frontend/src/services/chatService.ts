import type { ApiResponse } from '../types/router';

// Remove hardcoded URL - will be fetched dynamically
let SYFTBOX_BASE_URL: string | null = null;

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

interface SbUrlResponse {
  url: string;
}

class ChatService {
  private joinUrls(baseUrl: string, endpoint: string): string {
    // Remove trailing slash from base URL and leading slash from endpoint
    const cleanBase = baseUrl.replace(/\/$/, '');
    const cleanEndpoint = endpoint.replace(/^\//, '');
    return `${cleanBase}/${cleanEndpoint}`;
  }

  private async getServerUrl(): Promise<string> {
    if (SYFTBOX_BASE_URL) {
      return SYFTBOX_BASE_URL;
    }

    try {
      // Get the server URL from our backend
      const response = await fetch('/sburl');
      if (!response.ok) {
        throw new Error(`Failed to fetch server URL: ${response.status}`);
      }
      
      const data: SbUrlResponse = await response.json();
      // Trim trailing slash to prevent double slashes
      SYFTBOX_BASE_URL = data.url.replace(/\/$/, '');
      return SYFTBOX_BASE_URL;
    } catch (error) {
      console.error('Failed to fetch server URL, using fallback:', error);
      // Fallback to a default URL if the endpoint fails
      SYFTBOX_BASE_URL = 'https://dev.syftbox.net';
      return SYFTBOX_BASE_URL;
    }
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const serverUrl = await this.getServerUrl();
      const fullUrl = this.joinUrls(serverUrl, endpoint);
      const response = await fetch(fullUrl, {
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

  private async pollForResponse<T>(pollUrl: string, maxAttempts: number = 20): Promise<ApiResponse<T> & { errorDetails?: string }> {
    const serverUrl = await this.getServerUrl();
    
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      try {
        const fullUrl = this.joinUrls(serverUrl, pollUrl);
        const response = await fetch(fullUrl);
        let data: any = null;
        try {
          data = await response.json();
        } catch (jsonError) {
          // If response is not JSON, treat as error
          return {
            success: false,
            error: 'Something bad happened. Please try again later.',
            errorDetails: undefined,
          };
        }

        const statusCode = data?.data?.message?.status_code;
        const errorBody = data?.data?.message?.body || null;

        if (response.status === 200 && statusCode === 200) {
          return {
            success: true,
            data,
          };
        } else if (response.status === 202 || statusCode === 202) {
          // Still processing, wait and try again
          await new Promise(resolve => setTimeout(resolve, 2000));
          continue;
        } else {
          // Stop polling on any other status or error
          return {
            success: false,
            error: 'Something bad happened. Please try again later.',
            errorDetails: errorBody ?? undefined,
          };
        }
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error occurred',
          errorDetails: undefined,
        };
      }
    }

    return {
      success: false,
      error: 'Request timed out after maximum attempts',
      errorDetails: undefined,
    };
  }

  async search(routerName: string, author: string, query: string): Promise<ApiResponse<SearchResponse> & { errorDetails?: string }> {
    const encodedQuery = encodeURIComponent(query);
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/search?query="${encodedQuery}"`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);
    
    const endpoint = `/api/v1/send/msg?x-syft-url=${encodedSyftUrl}&x-syft-from=guest@syft.org`;
    
    const response = await this.request<SearchResponse>(endpoint, {
      method: 'POST',
    });

    // If we get a 202, poll for the response
    if (response.success && response.data?.data?.poll_url) {
      return this.pollForResponse<SearchResponse>(response.data.data.poll_url);
    }

    // Propagate errorDetails if present in the response
    let errorDetails: string | undefined = undefined;
    if (!response.success && typeof response.data?.data?.message?.body === 'string') {
      errorDetails = response.data.data.message.body;
    }
    return { ...response, errorDetails };
  }

  async chat(routerName: string, author: string, messages: ChatMessage[]): Promise<ApiResponse<ChatResponse>> {
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/chat`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);
    
    const endpoint = `/api/v1/send/msg?x-syft-url=${encodedSyftUrl}&x-syft-from=guest@syft.org`;
    
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