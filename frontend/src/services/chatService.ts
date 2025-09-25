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
        cost?: number;
        id?: string;
        providerInfo?: {
          provider: string;
        };
        query?: string;
        results?: SearchResult[];
      } | string; // Can be either JSON object or string (for error messages)
      created: string;
      expires: string;
      headers: {
        'content-length': string;
        'content-type': string;
      };
      id: string;
      method: string;
      sender: string;
      status_code: number;
      url: string;
    };
    poll_url?: string;
  };
}

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
  sources?: SearchResult[]; // Sources used for this specific message
}

interface ChatRequest {
  model: string;
  messages: ChatMessage[];
}

interface ChatResponse {
  request_id: string;
  data: {
    message: {
      status_code: number;
      body: {
        message?: {
          content: string;
        };
      } | string; // Can be either JSON object or string (for error messages)
      created: string;
      expires: string;
      headers: {
        'content-length': string;
        'content-type': string;
      };
      id: string;
      method: string;
      sender: string;
      url: string;
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

interface TransactionTokenResponse {
  token: string;
  recipient_email: string;
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

      let data: any = null;
      try {
        data = await response.json();
      } catch (jsonError) {
        // If response is not JSON, return error
        return {
          success: false,
          error: 'Invalid response format. Please try again later.',
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
        const messageBody = data?.data?.message?.body;

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
          // Handle case where message.body might not be JSON
          let errorDetails: string | undefined = undefined;
          if (messageBody) {
            if (typeof messageBody === 'string') {
              errorDetails = messageBody;
            } else if (typeof messageBody === 'object') {
              errorDetails = JSON.stringify(messageBody);
            }
          }
          
          return {
            success: false,
            error: 'Something bad happened. Please try again later.',
            errorDetails,
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

  async search(
    routerName: string, 
    author: string, 
    query: string,
    options?: { user_email?: string; transaction_token?: string }
  ): Promise<ApiResponse<SearchResponse> & { errorDetails?: string }> {
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/search`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);
    
    const endpoint = `/api/v1/send/msg?suffix-sender=true&x-syft-url=${encodedSyftUrl}&x-syft-from=guest@syftbox.net`;
    
    const payload: any = {
      query,
    };
    if (options?.user_email) payload.user_email = options.user_email;
    if (options?.transaction_token) payload.transaction_token = options.transaction_token;

    const response = await this.request<SearchResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // If we get a 202, poll for the response
    if (response.success && response.data?.data?.poll_url) {
      return this.pollForResponse<SearchResponse>(response.data.data.poll_url);
    }

    // Propagate errorDetails if present in the response
    let errorDetails: string | undefined = undefined;
    if (!response.success && response.data?.data?.message?.body) {
      const messageBody = response.data.data.message.body;
      if (typeof messageBody === 'string') {
        errorDetails = messageBody;
      } else if (typeof messageBody === 'object') {
        errorDetails = JSON.stringify(messageBody);
      }
    }
    return { ...response, errorDetails };
  }

  async createTransactionToken(recipient_email: string): Promise<string> {
    try {
      const response = await fetch(`/account/token/create?recipient_email=${encodeURIComponent(recipient_email)}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error('Failed to create transaction token');
      }
      const data: TransactionTokenResponse = await response.json();
      return data.token;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error occurred while creating transaction token');
    }
  }

  async chat(
    routerName: string,
    author: string,
    messages: ChatMessage[],
    options?: { user_email?: string; transaction_token?: string }
  ): Promise<ApiResponse<ChatResponse> & { errorDetails?: string }> {
    const syftUrl = `syft://${author}/app_data/${routerName}/rpc/chat`;
    const encodedSyftUrl = encodeURIComponent(syftUrl);

    const endpoint = `/api/v1/send/msg?suffix-sender=true&x-syft-url=${encodedSyftUrl}&x-syft-from=guest@syftbox.net`;

    const payload: any = {
      model: "tinyllama:latest",
      messages,
    };
    if (options?.user_email) payload.user_email = options.user_email;
    if (options?.transaction_token) payload.transaction_token = options.transaction_token;

    const response = await this.request<ChatResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    // If we get a 202, poll for the response
    if (response.success && response.data?.data?.poll_url) {
      return this.pollForResponse<ChatResponse>(response.data.data.poll_url);
    }

    // Propagate errorDetails if present in the response
    let errorDetails: string | undefined = undefined;
    if (!response.success && response.data?.data?.message?.body) {
      const messageBody = response.data.data.message.body;
      if (typeof messageBody === 'string') {
        errorDetails = messageBody;
      } else if (typeof messageBody === 'object') {
        errorDetails = JSON.stringify(messageBody);
      }
    }
    return { ...response, errorDetails };
  }

}

export const chatService = new ChatService();
export type { SearchResult, ChatMessage, SearchResponse, ChatResponse }; 