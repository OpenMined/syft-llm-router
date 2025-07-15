import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
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
        console.error('Error loading routers:', error);
      }
    };

    loadRouters();
  }, []);

  // Update lastSearchResults after each search
  // Remove the useEffect that referenced searchResults

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

  return (
    <div className="max-w-4xl mx-auto py-8">
      <Button variant="ghost" onClick={onBack} className="mb-8">&larr; Back</Button>
      
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <h1 className="text-2xl font-bold text-gray-900">Chat</h1>
          <p className="text-gray-600 mt-1">Ask questions and get answers from your data sources</p>
        </div>

        {/* Configuration */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Data Sources */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data Sources (Search)
              </label>
              <select
                multiple
                onChange={(e) => {
                  const target = e.target as HTMLSelectElement;
                  const selected = Array.from(target.selectedOptions, option => option.value);
                  setSelectedDataSources(selected);
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                size={3}
              >
                {searchRouters.map(router => (
                  <option key={router.name} value={router.name}>
                    {router.name} ({router.author})
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Select one or more data sources to search (optional)
              </p>
            </div>

            {/* Chat Source */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Chat Source *
              </label>
              <select
                value={selectedChatSource}
                onChange={(e) => setSelectedChatSource((e.target as HTMLSelectElement).value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select a chat source</option>
                {chatRouters.map(router => (
                  <option key={router.name} value={router.name}>
                    {router.name} ({router.author})
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Select a chat model to generate responses
              </p>
            </div>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="px-6 py-4 h-96 overflow-y-auto">
          {chatHistory.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p>Start a conversation by typing a message below</p>
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
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      {/* References section for assistant messages */}
                      {isAssistant && lastSearchResults.length > 0 && (
                        <div className="mt-2 text-xs text-gray-500">
                          <span className="font-semibold">Sources used: </span>
                          {Array.from(new Set(lastSearchResults.map(r => r.metadata?.filename))).map((filename, i) => {
                            const source = lastSearchResults.find(r => r.metadata?.filename === filename);
                            return (
                              <span key={filename} className="mr-2">
                                <span className="underline cursor-pointer" title={source ? source.content : 'No content found'}>
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
            <div className="flex justify-start">
              <div className="bg-gray-100 text-gray-900 max-w-xs lg:max-w-md px-4 py-2 rounded-lg">
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
            <div className="text-red-700 text-sm">{error}</div>
          </div>
        )}

        {/* Input */}
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex space-x-3">
            <textarea
              value={message}
              onChange={(e) => setMessage((e.target as HTMLTextAreaElement).value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message here..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={isLoading || !message.trim() || !selectedChatSource}
              loading={isLoading}
              className="self-end"
            >
              Send
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 