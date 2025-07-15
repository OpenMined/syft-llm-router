import { useState, useEffect } from 'preact/hooks';
import { Button } from '../shared/Button';
import { CreateRouterModal } from './CreateRouterModal';
import { PublishRouterModal } from './PublishRouterModal';
import { routerService } from '../../services/routerService';
import type { Router } from '../../types/router';
import type { ProfileType } from '../shared/ProfileToggle';

interface RouterListProps {
  onRouterClick?: (routerName: string, published: boolean, author: string) => void;
  profile: ProfileType;
}

export function RouterList({ onRouterClick, profile }: RouterListProps) {
  const [routers, setRouters] = useState<Router[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [publishModalRouter, setPublishModalRouter] = useState<string | null>(null);
  const [publishModalDetails, setPublishModalDetails] = useState<any>(null);

  const fetchRouters = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await routerService.listRouters();
      if (response.success && response.data) {
        setRouters(response.data);
      } else {
        setError(response.error || 'Failed to load routers');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRouters();
  }, []);

  const handleCreateSuccess = () => {
    fetchRouters(); // Refresh the list
  };

  const handlePublishClick = async (routerName: string) => {
    try {
      // Get current user to determine if this is their router
      const userResponse = await routerService.getUsername();
      if (userResponse.success && userResponse.data) {
        const currentUser = userResponse.data.username;
        
        // Find the router in the list to get the author
        const router = routers.find(r => r.name === routerName);
        if (router && router.author === currentUser) {
          // Fetch router details for pre-filling
          const detailsResponse = await routerService.getRouterDetails(routerName, currentUser, false);
          if (detailsResponse.success && detailsResponse.data) {
            setPublishModalDetails({
              summary: detailsResponse.data.metadata?.summary,
              description: detailsResponse.data.metadata?.description,
              tags: detailsResponse.data.metadata?.tags,
              services: detailsResponse.data.services?.map(service => ({
                type: service.type,
                pricing: service.pricing.toString(),
                charge_type: service.charge_type,
                enabled: service.enabled
              }))
            });
          }
        }
      }
      setPublishModalRouter(routerName);
    } catch (error) {
      console.error('Error fetching router details:', error);
      setPublishModalRouter(routerName); // Still open modal even if details fetch fails
    }
  };



  // Filter routers for client profile
  const visibleRouters = profile === 'client' ? routers.filter(r => r.published) : routers;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Routers</h1>
          <p className="text-gray-600 mt-1">Manage your AI router projects</p>
        </div>
        {profile === 'provider' && (
          <Button 
            variant="primary" 
            onClick={() => setShowCreateModal(true)}
            className="flex items-center space-x-2"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Create Router</span>
          </Button>
        )}
      </div>

      {/* Router List */}
      <div className="bg-white rounded-lg shadow-sm divide-y divide-gray-200">
        {loading ? (
          <div className="py-12 text-center text-gray-500">Loading routers...</div>
        ) : error ? (
          <div className="py-12 text-center text-error-600">{error}</div>
        ) : visibleRouters.length === 0 ? (
          <div className="py-12 text-center text-gray-500">No routers found. {profile === 'provider' ? 'Click "Create Router" to get started.' : ''}</div>
        ) : (
          <div className="space-y-6 py-4">
            {visibleRouters.map((router) => (
            <div
              key={router.name}
                className="flex flex-row items-stretch justify-between bg-white rounded-lg shadow border border-gray-100 hover:shadow-md transition p-6 gap-4"
            >
                {/* Left: Main Content */}
                <div className="flex flex-col flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-lg font-semibold text-gray-900 truncate">{router.name}</span>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      router.published 
                        ? 'bg-success-100 text-success-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {router.published ? 'Published' : 'Draft'}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    Author {router.author}
                  </div>
                  {router.summary && (
                    <div className="text-sm text-gray-700 max-w-md bg-gray-50 rounded px-3 py-2 mb-3 break-words">
                      {router.summary.split(' ').length > 50 
                        ? router.summary.split(' ').slice(0, 50).join(' ') + '...'
                        : router.summary
                      }
                    </div>
                  )}
                  {/* Services */}
                  {router.services && router.services.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-1">
                      {router.services
                        .filter(service => service.enabled)
                        .map((service) => (
                          <span
                            key={service.type}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                          >
                            <span className="capitalize mr-1">{service.type}:</span>
                            <span className="font-mono mr-1">${service.pricing}</span>
                            <span className="text-blue-600"> {service.charge_type.replace('_', ' ')}</span>
                          </span>
                        ))}
                    </div>
                  )}
                </div>
                {/* Right: Actions */}
                <div className="flex flex-col items-end justify-between min-w-[120px] ml-4">
                  <Button variant="ghost" size="sm" onClick={() => onRouterClick?.(router.name, router.published, router.author)}>
                    View Details
                  </Button>
                {profile === 'provider' && !router.published && (
                    <Button variant="primary" size="sm" className="mt-2" onClick={() => handlePublishClick(router.name)}>
                      Publish
                    </Button>
                )}
                </div>
              </div>
            ))}
            </div>
        )}
      </div>

      {/* Create Router Modal */}
      {profile === 'provider' && (
        <CreateRouterModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleCreateSuccess}
        />
      )}
      {/* Publish Router Modal */}
      {publishModalRouter && (
        <PublishRouterModal
          isOpen={!!publishModalRouter}
          onClose={() => {
            setPublishModalRouter(null);
            setPublishModalDetails(null);
            fetchRouters();
          }}
          routerName={publishModalRouter}
          routerDetails={publishModalDetails}
        />
      )}
    </div>
  );
} 