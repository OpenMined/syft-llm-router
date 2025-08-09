import { h } from 'preact';
import { useEffect, useState, useRef } from 'preact/hooks';
import { routerService } from '../../services/routerService';
import { GATEKEEPER_TERM } from '../../utils/constants';
import { useDelegateStatus } from '../../hooks/useDelegateStatus';
import type { DelegateStatus } from '../../types/router';

interface HeaderProps {
  profileToggle: h.JSX.Element;
  onTabChange?: (tab: 'routers' | 'chat' | 'usage') => void;
  activeTab?: 'routers' | 'chat' | 'usage';
  onGatekeeperStatusChange?: (status: DelegateStatus) => void;
}

export function Header({ profileToggle, onTabChange, activeTab = 'routers', onGatekeeperStatusChange }: HeaderProps) {
  const [username, setUsername] = useState<string>('Loading...');
  const [syftBoxUrl, setSyftBoxUrl] = useState<string | null>(null);
  const [accountInfo, setAccountInfo] = useState<{ id: string; email: string; balance: number } | null>(null);
  const [balance, setBalance] = useState<string | null>(null);
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [isOptingIn, setIsOptingIn] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Use the delegate status hook
  const { status: gatekeeperStatus, optIn } = useDelegateStatus();

  useEffect(() => {
    let mounted = true;
    routerService.getUsername().then((resp) => {
      if (mounted) {
        if (resp.success && resp.data?.username) {
          setUsername(resp.data.username);
        } else {
          setUsername('Unknown User');
        }
      }
    }).catch(() => setUsername('Unknown User'));
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    routerService.getSyftBoxUrl().then((resp) => {
      if (mounted && resp.success && resp.data) {
        setSyftBoxUrl(resp.data.url);
      }
    }).catch(() => {
      // Silently fail, URL won't be shown
    });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    let mounted = true;
    routerService.getAccountInfo().then((resp) => {
      if (mounted) {
        if (resp.success && resp.data) {
          setAccountInfo(resp.data);
          setBalance(resp.data.balance.toFixed(2));
        } else {
          setAccountInfo(null);
          setBalance(null);
        }
      }
    }).catch(() => {
      setAccountInfo(null);
      setBalance(null);
    });
    return () => { mounted = false; };
  }, []);

  // Notify parent when gatekeeper status changes
  useEffect(() => {
    if (gatekeeperStatus) {
      onGatekeeperStatusChange?.(gatekeeperStatus);
    }
  }, [gatekeeperStatus, onGatekeeperStatusChange]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowUserDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleOptInAsGatekeeper = async () => {
    setIsOptingIn(true);
    try {
      const result = await optIn();
      if (result.success) {
        setShowUserDropdown(false);
        alert('Successfully opted in as a Gatekeeper! You can now be assigned to manage routers.');
      } else {
        console.error('Failed to opt in as gatekeeper:', result.error);
        alert('Failed to opt in as Gatekeeper: ' + result.error);
      }
    } catch (error) {
      console.error('Error opting in as gatekeeper:', error);
      alert('Error opting in as Gatekeeper');
    } finally {
      setIsOptingIn(false);
    }
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center h-16 gap-6">
        {/* Logo and App Name */}
        <div className="flex items-center space-x-3">
          <img src="/static/syftbox-logo.svg" alt="SyftBox Logo" className="h-8 w-8" />
          <span className="text-xl font-bold text-gray-900 tracking-tight">SyftBox <span className="ml-1 text-xs font-semibold text-primary-600 align-top">ALPHA</span></span>
        </div>
        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-2 flex-grow justify-center">
          <button
            onClick={() => onTabChange?.('routers')}
            className={`px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              activeTab === 'routers'
                ? 'text-primary-700 bg-primary-50'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            Routers
          </button>
          <button
            onClick={() => onTabChange?.('chat')}
            className={`px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 flex items-center gap-2 ${
              activeTab === 'chat'
                ? 'text-primary-700 bg-primary-50'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => onTabChange?.('usage')}
            className={`px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 flex items-center gap-2 ${
              activeTab === 'usage'
                ? 'text-primary-700 bg-primary-50'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            Usage
          </button>
        </nav>
        
        {/* SyftBox Server URL */}
        {syftBoxUrl && (
          <div className="flex items-center bg-blue-50 px-3 py-1 rounded-md border border-blue-200">
            <svg 
              className="h-4 w-4 text-blue-500 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
              title="SyftBox Server URL"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <a 
              href={syftBoxUrl} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 hover:underline font-mono truncate max-w-32"
              title="SyftBox Server URL"
            >
              {syftBoxUrl.replace(/^https?:\/\//, '').replace(/\/$/, '')}
            </a>
          </div>
        )}
        
        {/* User Info and Profile Toggle */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-3 bg-gray-50 px-3 py-1 rounded-md border border-gray-200">
            <div className="flex flex-col">
              <div className="flex items-center space-x-2">
                {/* User icon with dropdown toggle */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setShowUserDropdown(!showUserDropdown)}
                    className="flex items-center space-x-1 hover:bg-gray-100 p-1 rounded transition-colors"
                    title="User menu"
                  >
                    <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <svg className="h-3 w-3 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  
                  {/* Dropdown Menu */}
                  {showUserDropdown && (
                    <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                      <div className="py-1">
                        <div className="px-4 py-2 border-b border-gray-100">
                          <p className="text-sm font-medium text-gray-900">{accountInfo?.email || username}</p>
                          {gatekeeperStatus?.is_delegate && (
                            <p className="text-xs text-primary-600 mt-1">✓ {GATEKEEPER_TERM}</p>
                          )}
                        </div>
                        
                        {!gatekeeperStatus?.is_delegate && (
                          <button
                            onClick={handleOptInAsGatekeeper}
                            disabled={isOptingIn}
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isOptingIn ? 'Opting in...' : `Opt in as ${GATEKEEPER_TERM}`}
                          </button>
                        )}
                        
                        {gatekeeperStatus?.delegated_routers && gatekeeperStatus.delegated_routers.length > 0 && (
                          <div className="px-4 py-2 border-t border-gray-100">
                            <p className="text-xs text-gray-500 mb-1">Managing:</p>
                            {gatekeeperStatus.delegated_routers.slice(0, 3).map(router => (
                              <p key={router} className="text-xs text-gray-700 truncate">• {router}</p>
                            ))}
                            {gatekeeperStatus.delegated_routers.length > 3 && (
                              <p className="text-xs text-gray-500">+{gatekeeperStatus.delegated_routers.length - 3} more</p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
                
                <span className="text-xs text-gray-700">
                  User: <span className="font-medium">{accountInfo?.email || username}</span>
                </span>
              </div>
              <div className="flex items-center space-x-2 mt-1">
                {/* Dollar icon */}
                <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
                <span className="text-xs text-gray-700">
                  Balance: <span className="text-gray-500">{balance === null ? '...' : `$${balance}`}</span>
                </span>
              </div>
            </div>
            {profileToggle}
          </div>
        </div>
      </div>
    </header>
  );
} 