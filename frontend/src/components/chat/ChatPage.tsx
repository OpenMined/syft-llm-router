import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { Button } from '../shared/Button';
import { chatService, type SearchResult, type ChatMessage } from '../../services/chatService';
import { routerService } from '../../services/routerService';
import type { Router } from '../../types/router';

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

// Single Select Dropdown Component
interface SingleSelectDropdownProps {
  options: Router[];
  selected: string;
  onSelect: (value: string) => void;
  placeholder: string;
  type: 'search' | 'chat';
}

function SingleSelectDropdown({ options, selected, onSelect, placeholder, type }: SingleSelectDropdownProps) {
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
    return {
      isEnabled: service?.enabled || false,
      pricing: service?.pricing || 0
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
              const { isEnabled, pricing } = getRouterStatus(router);
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
                          isEnabled 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {isEnabled ? '✓ Available' : '✗ Disabled'}
                        </span>
                        {pricing > 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                            ${pricing}/req
                          </span>
                        )}
                        {pricing === 0 && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
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
}

function MultiSelectDropdown({ options, selected, onToggle, placeholder, type }: MultiSelectDropdownProps) {
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
    return {
      isEnabled: service?.enabled || false,
      pricing: service?.pricing || 0
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
                const { isEnabled, pricing } = getRouterStatus(router);
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
                            isEnabled 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {isEnabled ? '✓ Available' : '✗ Disabled'}
                          </span>
                          {pricing > 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                              ${pricing}/req
                            </span>
                          )}
                          {pricing === 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
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
  
  // Available routers
  const [routers, setRouters] = useState<Router[]>([]);
  const [searchRouters, setSearchRouters] = useState<Router[]>([]);
  const [chatRouters, setChatRouters] = useState<Router[]>([]);
  
  // Selected routers
  const [selectedDataSources, setSelectedDataSources] = useState<string[]>([]);
  const [selectedChatSource, setSelectedChatSource] = useState<string>('');

  // Add a ref to keep track of the latest searchResults for tooltips
  const [lastSearchResults, setLastSearchResults] = useState<SearchResult[]>([]);

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

  const handleSendMessage = async () => {
    if (!message.trim() || !selectedChatSource) {
      setError('Please enter a message and select a chat source');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      let enhancedMessage = message;
      const uniqueFiles = new Set<string>();
      let searchResults: SearchResult[] = [];

      // If data sources are selected, search them first
      if (selectedDataSources.length > 0) {
        
        // Search each selected data source
        for (const routerName of selectedDataSources) {
          const router = searchRouters.find(r => r.name === routerName);
          if (router) {
            try {
              const searchResponse = await chatService.search(router.name, router.author, message);
              if (searchResponse.success && searchResponse.data) {
                const results = searchResponse.data.data.message.body.results;
                searchResults.push(...results);
                
                // Collect unique filenames
                results.forEach((result: SearchResult) => {
                  if (result.metadata?.filename) {
                    uniqueFiles.add(result.metadata.filename);
                  }
                });
              }
            } catch (error) {
              console.error(`Error searching router ${routerName}:`, error);
            }
          }
        }

        // Collect search results for context
        if (searchResults.length > 0) {
          const sourceContent = searchResults
            .map((result: SearchResult) => result.content)
            .join('\n\n');
          
          enhancedMessage = sourceContent;
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

      // Prepare messages for chat
      const messages: ChatMessage[] = [
        {
          role: 'system',
          content: `You are a helpful AI assistant that answers questions based on the provided source context.

Use the provided sources to answer the user's question accurately and comprehensively. If you do not know the answer from the sources, say so.`
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
      const chatResponse = await chatService.chat(chatRouter.name, chatRouter.author, messages);
      
      if (chatResponse.success && chatResponse.data) {
        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: chatResponse.data.data.message.body.message.content
        };
        setChatHistory(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(chatResponse.error || 'Failed to get chat response');
      }

      // Clear the input
      setMessage('');

    } catch (error) {
      console.error('Error in chat:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: KeyboardEvent) => {
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
              <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
              <p className="text-gray-600 mt-1">Discover insights from the data sources that matter to you</p>
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
                          <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
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
                  <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </div>
              </div>
            )}

            {/* Input */}
            <div className="px-6 py-4 border-t border-gray-200">
              <div className="flex space-x-3">
                <div className="flex-1 relative">
                  <textarea
                    value={message}
                    onChange={(e) => setMessage((e.target as HTMLTextAreaElement).value)}
                    onKeyPress={handleKeyPress}
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
                  className="self-end px-6 py-3 rounded-xl"
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
                    />
                    
                    {/* Preview of available sources */}
                    <div className="mt-4 space-y-2">
                      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Check out latest sources..</p>
                      <div className="space-y-2">
                        {searchRouters.slice(0, 3).map((router) => {
                          const service = router.services.find(s => s.type === 'search');
                          const isEnabled = service?.enabled || false;
                          const pricing = service?.pricing || 0;
                          
                          return (
                            <div key={router.name} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-gray-900 text-sm truncate">{router.name}</div>
                                <div className="text-xs text-gray-500 truncate">by {router.author}</div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  isEnabled 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                                }`}>
                                  {isEnabled ? '✓' : '✗'}
                                </span>
                                {pricing === 0 && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    Free
                                  </span>
                                )}
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