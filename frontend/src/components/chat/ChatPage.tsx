import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { Button } from '../shared/Button';
import { chatService, type SearchResult, type ChatMessage } from '../../services/chatService';
import { routerService } from '../../services/routerService';
import type { Router } from '../../types/router';
import { useRouterHealth } from '../../hooks/useRouterHealth';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

interface ChatPageProps {
  onBack: () => void;
}

// Helper to extract [filename] references from a string
function extractFilenames(text: string): string[] {
  const matches = text.match(/\[([^\]]+)\]/g);
  if (!matches) return [];
  // Remove brackets
  return Array.from(new Set(matches.map(m => m.slice(1, -1))));
}

// Helper to safely render markdown content
function renderMarkdown(content: string): string {
  // Handle both sync and async marked behavior
  const rawHtml = marked(content) as string;
  return DOMPurify.sanitize(rawHtml);
}

// Single Select Dropdown Component
interface SingleSelectDropdownProps {
  options: Router[];
  selected: string;
  onSelect: (value: string) => void;
  placeholder: string;
  type: 'search' | 'chat';
  getRouterHealth: (routerName: string) => 'online' | 'offline' | 'unknown';
  isRouterChecking: (routerName: string) => boolean;
}

function SingleSelectDropdown({ options, selected, onSelect, placeholder, type, getRouterHealth, isRouterChecking }: SingleSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedRouter = options.find(r => r.name === selected);

  const getRouterStatus = (router: Router) => {
    const service = router.services.find(s => s.type === type);
    const healthStatus = getRouterHealth(router.name);
    return {
      isEnabled: service?.enabled || false,
      pricing: service?.pricing || 0,
      healthStatus
    };
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        className="w-full px-4 py-3 text-left bg-white border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:bg-gray-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          {selectedRouter ? (
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900 truncate">{selectedRouter.name}</div>
              <div className="text-sm text-gray-500 truncate">by {selectedRouter.author}</div>
            </div>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-auto">
          {options.length === 0 ? (
            <div className="px-4 py-3 text-gray-500 text-center">No options available</div>
          ) : (
            options.map((router) => {
              const { isEnabled, pricing, healthStatus } = getRouterStatus(router);
              return (
                <button
                  key={router.name}
                  type="button"
                  className={`w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 ${
                    selected === router.name ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                  } ${!isEnabled ? 'opacity-60' : ''}`}
                  onClick={() => {
                    onSelect(router.name);
                    setIsOpen(false);
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 truncate">{router.name}</div>
                      <div className="text-sm text-gray-500 truncate">by {router.author}</div>
                      <div className="mt-1 flex items-center space-x-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          healthStatus === 'online' 
                            ? 'bg-green-100 text-green-800' 
                            : healthStatus === 'offline'
                            ? 'bg-red-100 text-red-800'
                            : isRouterChecking(router.name)
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {healthStatus === 'online' ? '🟢 Online' : healthStatus === 'offline' ? '🔴 Offline' : isRouterChecking(router.name) ? '⏳ Checking...' : '⚪ Unknown'}
                        </span>
                        {pricing > 0 && (
                          <span className="inline-flex items-center px-2 py-1 text-xs text-gray-600">
                            ${pricing}/req
                          </span>
                        )}
                        {pricing === 0 && (
                          <span className="inline-flex items-center px-2 py-1 text-xs text-gray-600">
                            Free
                          </span>
                        )}
                      </div>
                    </div>
                    {selected === router.name && (
                      <div className="ml-2">
                        <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        </div>
                      </div>
                    )}
                  </div>
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

// Multi Select Dropdown Component
interface MultiSelectDropdownProps {
  options: Router[];
  selected: string[];
  onToggle: (value: string) => void;
  placeholder: string;
  type: 'search' | 'chat';
  getRouterHealth: (routerName: string) => 'online' | 'offline' | 'unknown';
  isRouterChecking: (routerName: string) => boolean;
}

function MultiSelectDropdown({ options, selected, onToggle, placeholder, type, getRouterHealth, isRouterChecking }: MultiSelectDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getRouterStatus = (router: Router) => {
    const service = router.services.find(s => s.type === type);
    const healthStatus = getRouterHealth(router.name);
    return {
      isEnabled: service?.enabled || false,
      pricing: service?.pricing || 0,
      healthStatus
    };
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        className="w-full px-4 py-3 text-left bg-white border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 hover:bg-gray-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          {selected.length > 0 ? (
            <div className="flex-1 min-w-0">
              <div className="font-medium text-gray-900">
                {selected.length} source{selected.length > 1 ? 's' : ''} selected
              </div>
              <div className="text-sm text-gray-500 truncate">
                {selected.slice(0, 2).join(', ')}
                {selected.length > 2 && ` +${selected.length - 2} more`}
              </div>
            </div>
          ) : (
            <span className="text-gray-500">{placeholder}</span>
          )}
          <svg
            className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-64 overflow-auto">
          {options.length === 0 ? (
            <div className="px-4 py-3 text-gray-500 text-center">No options available</div>
          ) : (
            <>
              {selected.length > 0 && (
                <div className="px-4 py-2 border-b border-gray-200">
                  <button
                    type="button"
                    className="text-sm text-blue-600 hover:text-blue-800"
                    onClick={() => {
                      selected.forEach(name => onToggle(name));
                    }}
                  >
                    Clear all selections
                  </button>
                </div>
              )}
              {options.map((router) => {
                const { isEnabled, pricing, healthStatus } = getRouterStatus(router);
                const isSelected = selected.includes(router.name);
                return (
                  <button
                    key={router.name}
                    type="button"
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 ${
                      isSelected ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    } ${!isEnabled ? 'opacity-60' : ''}`}
                    onClick={() => onToggle(router.name)}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 truncate">{router.name}</div>
                        <div className="text-sm text-gray-500 truncate">by {router.author}</div>
                        <div className="mt-1 flex items-center space-x-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            healthStatus === 'online' 
                              ? 'bg-green-100 text-green-800' 
                              : healthStatus === 'offline'
                              ? 'bg-red-100 text-red-800'
                              : isRouterChecking(router.name)
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {healthStatus === 'online' ? '🟢 Online' : healthStatus === 'offline' ? '🔴 Offline' : isRouterChecking(router.name) ? '⏳ Checking...' : '⚪ Unknown'}
                          </span>
                          {pricing > 0 && (
                            <span className="inline-flex items-center px-2 py-1 text-xs text-gray-600">
                              ${pricing}/req
                            </span>
                          )}
                          {pricing === 0 && (
                            <span className="inline-flex items-center px-2 py-1 text-xs text-gray-600">
                              Free
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="ml-2 flex items-center">
                        <div className={`w-5 h-5 border-2 rounded flex items-center justify-center ${
                          isSelected 
                            ? 'bg-blue-500 border-blue-500' 
                            : 'border-gray-300'
                        }`}>
                          {isSelected && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export function ChatPage({ onBack }: ChatPageProps) {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | undefined>(undefined);
  const [showErrorDetails, setShowErrorDetails] = useState(false);
  
  // Available routers
  const [routers, setRouters] = useState<Router[]>([]);
  const [searchRouters, setSearchRouters] = useState<Router[]>([]);
  const [chatRouters, setChatRouters] = useState<Router[]>([]);
  
  // Selected routers
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);
  const [selectedChatSource, setSelectedChatSource] = useState<string>('');

  // Add a ref to keep track of the latest searchResults for tooltips
  const [lastSearchResults, setLastSearchResults] = useState<SearchResult[]>([]);

  // Add state for user email
  const [userEmail, setUserEmail] = useState<string | null>(null);

  // Health checking for all routers
  const { getRouterHealth, isRouterChecking, isChecking: isHealthChecking } = useRouterHealth([...searchRouters, ...chatRouters], {
    checkInterval: 30000, // Check every 5 minutes
    enabled: true
  });

  // Calculate total price for selected items
  const calculateTotalPrice = () => {
    let total = 0;
    
    // Add pricing for selected data sources (search services)
    selectedDataSources.forEach(sourceName => {
      const router = searchRouters.find(r => r.name === sourceName);
      if (router) {
        const searchService = router.services.find(s => s.type === 'search');
        if (searchService) {
          total += searchService.pricing || 0;
        }
      }
    });
    
    // Add pricing for selected chat source
    if (selectedChatSource) {
      const router = chatRouters.find(r => r.name === selectedChatSource);
      if (router) {
        const chatService = router.services.find(s => s.type === 'chat');
        if (chatService) {
          total += chatService.pricing || 0;
        }
      }
    }
    
    return total;
  };

  // Load available routers
  useEffect(() => {
    const loadRouters = async () => {
      try {
        const response = await routerService.listRouters();
        if (response.success && response.data) {
          const allRouters = response.data;
          setRouters(allRouters);
          
          // Filter routers with search service
          const searchRouters = allRouters.filter(router => 
            router.published && 
            router.services.some(service => service.type === 'search' && service.enabled)
          );
          setSearchRouters(searchRouters);
          
          // Filter routers with chat service
          const chatRouters = allRouters.filter(router => 
            router.published && 
            router.services.some(service => service.type === 'chat' && service.enabled)
          );
          setChatRouters(chatRouters);
        }
      } catch (error) {
        console.error('❌ [ChatPage] Error loading routers:', error);
      }
    };

    loadRouters();
  }, []);

  // In useEffect, fetch user email on mount
  useEffect(() => {
    routerService.getUsername().then((resp) => {
      if (resp.success && resp.data?.username) {
        setUserEmail(resp.data.username);
      }
    });
  }, []);

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedChatSource) {
      setError('Please enter a message and select a chat source');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const uniqueFiles = new Set<string>();
      let searchResults: SearchResult[] = [];

      // If data sources are selected, search them first
      if (selectedDataSources.length > 0) {
        
        // Search each selected data source
        for (const routerName of selectedDataSources) {
          const router = searchRouters.find(r => r.name === routerName);
          if (router) {
            try {
              // Check if search service has pricing
              const searchService = router.services.find(s => s.type === 'search');
              const searchPricing = searchService?.pricing || 0;
              
              let searchTransactionToken: string | undefined = undefined;
              if (searchPricing > 0) {
                if (!userEmail) throw new Error('User email not found');
                try {
                  searchTransactionToken = await chatService.createTransactionToken(router.author);
                } catch (err) {
                  console.error(`Failed to create transaction token for search service ${routerName}:`, err);
                  continue; // Skip this search service if token creation fails
                }
              }

              const searchResponse = await chatService.search(
                router.name, 
                router.author, 
                message,
                { user_email: userEmail!, ...(searchPricing > 0 ? { transaction_token: searchTransactionToken } : {}) }
              );
              
              if (searchResponse.success && searchResponse.data) {
                // Check if the response has a successful status code
                const statusCode = searchResponse.data?.data?.message?.status_code;
                if (statusCode !== 200) {
                  console.warn(`Search request failed for router ${routerName} with status code: ${statusCode}`);
                  continue; // Skip this search service and try the next one
                }
                
                // Safely extract search results with proper error handling
                const messageBody = searchResponse.data?.data?.message?.body;
                if (typeof messageBody === 'string') {
                  // Body is a string (error message)
                  console.warn(`Search request failed for router ${routerName}:`, messageBody);
                  continue; // Skip this search service and try the next one
                }
                
                const results = messageBody?.results;
                if (results && Array.isArray(results)) {
                  searchResults.push(...results);
                  
                  // Collect unique filenames
                  results.forEach((result: SearchResult) => {
                    if (result.metadata?.filename) {
                      uniqueFiles.add(result.metadata.filename);
                    }
                  });
                } else {
                  console.warn(`Invalid search results format for router ${routerName}:`, searchResponse.data);
                }
              }
            } catch (error) {
              console.error(`Error searching router ${routerName}:`, error);
            }
          }
        }

        // Update lastSearchResults state for tooltips
        setLastSearchResults(searchResults);
      }

      // Add user message to chat history
      const userMessage: ChatMessage = { role: 'user', content: message };
      setChatHistory(prev => [...prev, userMessage]);

      // Find the selected chat router
      const chatRouter = chatRouters.find(r => r.name === selectedChatSource);
      if (!chatRouter) {
        throw new Error('Selected chat source not found');
      }

      // Find the chat service for pricing
      const chatServiceObj = chatRouter.services.find(s => s.type === 'chat');
      const chatPricing = chatServiceObj?.pricing || 0;
      const recipientEmail = chatRouter.author;

      let transactionToken: string | undefined = undefined;
      if (chatPricing > 0) {
        if (!userEmail) throw new Error('User email not found');
        try {
          transactionToken = await chatService.createTransactionToken(recipientEmail);
        } catch (err) {
          setError('Failed to create transaction token.');
          setErrorDetails(err instanceof Error ? err.message : String(err));
          setShowErrorDetails(false);
          setIsLoading(false);
          return;
        }
      }

      // Prepare messages for chat
      const messages: ChatMessage[] = [
        {
          role: 'system',
          content: `You are a helpful AI assistant that can answer questions using both provided sources and your general knowledge.\n\nWhen sources are provided, use them as your primary information and supplement with your general knowledge when helpful. If you don't know the answer from the sources, you can still use your general knowledge to provide a helpful response.\n\nWhen no sources are provided, rely on your general knowledge to answer the question comprehensively.`
        },
        ...chatHistory,
        { role: 'user', content: message }
      ];

      // If we have search results, add them as a separate system message for context
      if (selectedDataSources.length > 0 && searchResults.length > 0) {
        // Format each result as [filename]\n<content>
        const formattedContext = searchResults
          .map((result: SearchResult) => `[${result.metadata?.filename || 'unknown'}]\n${result.content}`)
          .join('\n\n');
        
        messages.splice(-1, 0, {
          role: 'system',
          content: `Here is relevant source context to help answer the user's question:\n\n${formattedContext}`
        });
      }

      // Send chat request
      const chatResponse = await chatService.chat(
        chatRouter.name,
        chatRouter.author,
        messages,
        { user_email: userEmail!, ...(chatPricing > 0 ? { transaction_token: transactionToken } : {}) }
      );
      
      if (chatResponse.success && chatResponse.data) {
        // Check if the response has a successful status code
        const statusCode = chatResponse.data?.data?.message?.status_code;
        if (statusCode !== 200) {
          setError(`Chat request failed with status code: ${statusCode}`);
          setErrorDetails(`The chat service returned an error status code: ${statusCode}`);
          setShowErrorDetails(false);
          setIsLoading(false);
          return;
        }
        
        // Safely extract the content with proper error handling
        const messageBody = chatResponse.data?.data?.message?.body;
        if (typeof messageBody === 'string') {
          // Body is a string (error message)
          setError('Chat service returned an error.');
          setErrorDetails(messageBody);
          setShowErrorDetails(false);
          setIsLoading(false);
          return;
        }
        
        const messageContent = messageBody?.message?.content;
        if (!messageContent) {
          setError('Invalid response format from chat service. Please try again.');
          setErrorDetails('The response did not contain the expected message content.');
          setShowErrorDetails(false);
          setIsLoading(false);
          return;
        }
        
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: messageContent
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      } else {
        // Show improved error message from chatService
        setError(chatResponse.error || 'Something bad happened. Please try again later.');
        setErrorDetails((chatResponse as typeof chatResponse & { errorDetails?: string }).errorDetails);
        setShowErrorDetails(false);
        setIsLoading(false);
        return;
      }

      // Clear the input
      setMessage('');

    } catch (error) {
      console.error('Error in chat:', error);
      let errorMessage = 'An error occurred';
      
      if (error instanceof Error) {
        if (error.message.includes('message not found')) {
          errorMessage = 'Server error: The selected router service is currently unavailable. Please try a different router or try again later.';
        } else if (error.message.includes('500')) {
          errorMessage = 'Server error: The router service is experiencing issues. Please try again later.';
        } else {
          errorMessage = error.message;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleDataSourceToggle = (routerName: string) => {
    setSelectedDataSources(prev => 
      prev.includes(routerName) 
        ? prev.filter(name => name !== routerName)
        : [...prev, routerName]
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-8 px-4">
        <Button variant="ghost" onClick={onBack} className="mb-6">&larr; Back</Button>
        
        <div className="flex gap-6 h-[calc(100vh-120px)]">
          {/* Main Chat Area */}
          <div className="flex-1 bg-white rounded-lg shadow-sm border border-gray-200 flex flex-col">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
                  <p className="text-gray-600 mt-1">Discover insights from the data sources that matter to you</p>
                </div>
                <div className="text-right">
                  {(selectedDataSources.length > 0 || selectedChatSource) && (
                    <div className="text-sm text-gray-500">
                      <div>Cost per request: {calculateTotalPrice() === 0 ? (
                        <span className="text-green-600 font-medium">Free</span>
                      ) : (
                        <span className="text-gray-700 font-medium">${calculateTotalPrice().toFixed(2)}</span>
                      )}</div>
                    </div>
                  )}
                  {isHealthChecking && (
                    <div className="text-sm text-blue-500 mt-1">
                      <div className="flex items-center">
                        <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-500 mr-1"></div>
                        Checking router health...
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 px-6 py-4 overflow-y-auto">
              {chatHistory.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center text-gray-500">
                    <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <p className="text-lg font-medium">Start a conversation</p>
                    <p className="text-sm mt-1">Select a chat model and optionally data sources to begin</p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {chatHistory.map((msg, index) => {
                    const isAssistant = msg.role === 'assistant';
                    let references: string[] = [];
                    if (isAssistant) {
                      references = extractFilenames(msg.content);
                    }
                    return (
                      <div
                        key={index}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-2xl px-4 py-3 rounded-2xl ${
                            msg.role === 'user'
                              ? 'bg-blue-500 text-white rounded-br-md'
                              : 'bg-gray-100 text-gray-900 rounded-bl-md'
                          }`}
                        >
                          {msg.role === 'user' ? (
                            <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                          ) : (
                            <div 
                              className="text-sm leading-relaxed markdown-content"
                              dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                            />
                          )}
                          {/* References section for assistant messages */}
                          {isAssistant && lastSearchResults.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                              <span className="font-semibold">Sources: </span>
                              {Array.from(new Set(lastSearchResults.map(r => r.metadata?.filename))).map((filename, i) => {
                                const source = lastSearchResults.find(r => r.metadata?.filename === filename);
                                return (
                                  <span key={filename} className="mr-2">
                                    <span className="underline cursor-pointer hover:text-gray-800" title={source ? source.content : 'No content found'}>
                                      {filename}
                                    </span>
                                    {i < Array.from(new Set(lastSearchResults.map(r => r.metadata?.filename))).length - 1 && ','}
                                  </span>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              
              {isLoading && (
                <div className="flex justify-start mt-4">
                  <div className="bg-gray-100 text-gray-900 max-w-xs px-4 py-3 rounded-2xl rounded-bl-md">
                    <div className="flex items-center space-x-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                      <span className="text-sm">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-6 py-3 bg-red-50 border-t border-red-200">
                <div className="text-red-700 text-sm flex items-center">
                  <svg className="w-5 h-5 text-red-600 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.72-1.36 3.485 0l6.518 11.59c.75 1.334-.213 2.987-1.742 2.987H3.48c-1.53 0-2.492-1.653-1.742-2.987l6.519-11.59zM11 13a1 1 0 10-2 0 1 1 0 002 0zm-1-2a1 1 0 01-1-1V7a1 1 0 112 0v3a1 1 0 01-1 1z" clipRule="evenodd" />
                  </svg>
                  <span>{error}</span>
                  {errorDetails && (
                    <button
                      className="ml-2 underline text-xs text-red-700 hover:text-red-900"
                      onClick={() => setShowErrorDetails((v) => !v)}
                    >
                      {showErrorDetails ? 'Hide details' : 'See more information'}
                    </button>
                  )}
                </div>
                {showErrorDetails && errorDetails && (
                  <pre className="mt-2 bg-red-100 text-xs p-2 rounded whitespace-pre-wrap break-all">{errorDetails}</pre>
                )}
              </div>
            )}

            {/* Input */}
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex space-x-3">
                <div className="flex-1 relative">
                  <textarea
                    value={message}
                    onInput={(e) => setMessage(e.currentTarget.value)}
                    onChange={(e) => setMessage(e.currentTarget.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Type your message here..."
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none bg-gray-50 focus:bg-white transition-colors"
                    rows={3}
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={isLoading || !message.trim() || !selectedChatSource}
                  loading={isLoading}
                  className="self-start px-6 py-3 rounded-xl"
                >
                  Send
                </Button>
              </div>
            </div>
          </div>

          {/* Right Sidebar - Model Selection */}
          <div className="w-80 space-y-6">
            {/* Chat Model Selection */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Chat Model</h3>
                  <p className="text-sm text-gray-600">Select model for final prediction</p>
                </div>
              </div>
              
              <div className="space-y-3">
                {chatRouters.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4-4-4m0 8l4-4 4 4" />
                    </svg>
                    <p className="text-sm">No chat models available</p>
                  </div>
                ) : (
                  <SingleSelectDropdown
                    options={chatRouters}
                    selected={selectedChatSource}
                    onSelect={setSelectedChatSource}
                    placeholder="Select a chat model"
                    type="chat"
                    getRouterHealth={getRouterHealth}
                    isRouterChecking={isRouterChecking}
                  />
                )}
              </div>
            </div>

            {/* Data Sources Selection */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Data Sources</h3>
                  <p className="text-sm text-gray-600">Optional search sources</p>
                </div>
              </div>
              
              <div className="space-y-3">
                {searchRouters.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <svg className="mx-auto h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4-4-4m0 8l4-4 4 4" />
                    </svg>
                    <p className="text-sm">No search sources available</p>
                  </div>
                ) : (
                  <>
                    <MultiSelectDropdown
                      options={searchRouters}
                      selected={selectedDataSources}
                      onToggle={handleDataSourceToggle}
                      placeholder="Select data sources"
                      type="search"
                      getRouterHealth={getRouterHealth}
                      isRouterChecking={isRouterChecking}
                    />
                    
                    {/* Preview of available sources */}
                    <div className="mt-4 space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Check out latest sources..</p>
                      <div className="space-y-2">
                        {searchRouters.slice(0, 3).map((router) => {
                          const healthStatus = getRouterHealth(router.name);
                          
                          return (
                            <div key={router.name} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-gray-900 text-sm truncate">{router.name}</div>
                                <div className="text-xs text-gray-500 truncate">by {router.author}</div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  healthStatus === 'online' 
                                    ? 'bg-green-100 text-green-800' 
                                    : healthStatus === 'offline'
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {healthStatus === 'online' ? '🟢' : healthStatus === 'offline' ? '🔴' : '⚪'}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                        
                        {searchRouters.length > 3 && (
                          <div className="text-center py-2">
                            <span className="text-xs text-gray-500">
                              +{searchRouters.length - 3} more sources available
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 