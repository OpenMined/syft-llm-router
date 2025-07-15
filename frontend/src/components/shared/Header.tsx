import { h } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import { routerService } from '../../services/routerService';

interface HeaderProps {
  profileToggle: h.JSX.Element;
}

export function Header({ profileToggle }: HeaderProps) {
  const [username, setUsername] = useState<string>('Loading...');
  const [syftBoxUrl, setSyftBoxUrl] = useState<string | null>(null);

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

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
        {/* Logo and App Name */}
        <div className="flex items-center space-x-3">
          <img src="/syftbox-logo.svg" alt="SyftBox Logo" className="h-8 w-8" />
          <span className="text-xl font-bold text-gray-900 tracking-tight">SyftBox <span className="ml-1 text-xs font-semibold text-primary-600 align-top">ALPHA</span></span>
        </div>
        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-2">
          <a href="#" className="px-4 py-2 rounded-md text-sm font-medium text-primary-700 bg-primary-50 hover:bg-primary-100 focus:outline-none focus:ring-2 focus:ring-primary-500">Routers</a>
          <a href="#" className="px-4 py-2 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 flex items-center gap-2">
            Chat
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200">Coming Soon</span>
          </a>
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
            <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 15c2.5 0 4.847.655 6.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
            <span className="text-xs text-gray-700">User: <span className="font-medium">{username}</span></span>
            {profileToggle}
          </div>
          <div className="flex items-center space-x-2 bg-gray-50 px-3 py-1 rounded-md border border-gray-200">
            <span className="text-xs text-gray-700">Balance:</span>
            <span className="text-xs text-gray-500">$20</span>
          </div>
        </div>
      </div>
    </header>
  );
} 