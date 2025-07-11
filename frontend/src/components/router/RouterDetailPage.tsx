
import { useEffect, useState } from 'preact/hooks';
import { routerService } from '../../services/routerService';
import { Button } from '../shared/Button';
import type { ProfileType } from '../shared/ProfileToggle';
import { useTheme, themeClass } from '../shared/ThemeContext';
import { PublishRouterModal } from './PublishRouterModal';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import type { RouterDetails as RouterDetailsType, ServiceOverview, EndpointInfo } from '../../types/router';

interface RouterDetailProps {
  routerName: string;
  published: boolean;
  onBack: () => void;
  profile: ProfileType;
}

interface RouterDetails {
  name: string;
  published: boolean;
  services?: ServiceOverview[];
  metadata?: RouterDetailsType['metadata'];
  endpoints?: Record<string, EndpointInfo>;
}

function getMarkdownHtml(md: string) {
  try {
    if (typeof marked.parseInline === 'function') {
      const result = marked.parseInline(md);
      if (typeof result === 'string') return result;
      return '';
    }
    const result = marked(md);
    if (typeof result === 'string') return result;
    return '';
  } catch {
    return '';
  }
}

// Utility to format router names (snake_case or kebab-case to Title Case)
function formatRouterName(name: string): string {
  return name
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function RouterDetailPage({ routerName, published, onBack, profile }: RouterDetailProps) {
  const [details, setDetails] = useState<RouterDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'documentation'>('overview');
  const { color } = useTheme();
  const t = themeClass(color);
  const [showPublishModal, setShowPublishModal] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(null);
    routerService.getUsername().then(usernameResp => {
      if (usernameResp.success && usernameResp.data) {
        return routerService.getRouterDetails(routerName, usernameResp.data.username, published);
      } else {
        throw new Error('Failed to get username');
      }
    })
      .then((resp) => {
        if (resp.success && resp.data) {
          setDetails(resp.data);
        } else {
          setError(resp.error || 'Failed to load router details.');
        }
      })
      .catch(() => setError('Failed to load router details.'))
      .finally(() => setLoading(false));
  }, [routerName, published]);

  // If client tries to access a draft, show error
  if (profile === 'client' && !published) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <Button variant="ghost" onClick={onBack} className="mb-6">&larr; Back to Dashboard</Button>
        <div className="text-center text-error-600 py-12">You do not have access to this router. Only published routers are available in client mode.</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8">
      <Button variant="ghost" onClick={onBack} className="mb-8">&larr; Back</Button>
      {loading ? (
        <div className="py-12 text-center text-gray-500">Loading router details...</div>
      ) : error ? (
        <div className="py-12 text-center text-error-600">{error}</div>
      ) : details && (
        <>
          {/* Tabs */}
          <div className="flex space-x-8 border-b border-gray-200 mb-10">
            <button className={`px-4 py-2 text-base font-semibold border-b-2 transition-colors duration-200 ${activeTab === 'overview' ? t.border600 + ' ' + t.text600 : 'border-transparent text-gray-400'} bg-white focus:outline-none`} onClick={() => setActiveTab('overview')}>Overview</button>
            <button className={`px-4 py-2 text-base font-semibold border-b-2 transition-colors duration-200 ${activeTab === 'documentation' ? t.border600 + ' ' + t.text600 : 'border-transparent text-gray-400'} bg-white focus:outline-none`} onClick={() => setActiveTab('documentation')}>Documentation</button>
            <button className="px-4 py-2 text-base font-semibold text-gray-400 cursor-not-allowed flex items-center gap-2" disabled>
              Usage
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200 ml-2">Coming Soon</span>
            </button>
          </div>

          {activeTab === 'overview' && (
            <div className="flex flex-col md:flex-row gap-12">
              {/* Left Column: Summary, Tags, Meta */}
              <div className="flex-1 space-y-8">
                {/* Header */}
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">{formatRouterName(details.name)}</h2>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${details.published ? t.bg50 + ' ' + t.text600 : 'bg-gray-100 text-gray-800'} border ${details.published ? t.border600 : 'border-gray-200'}`}>{details.published ? 'Published' : 'Draft'}</span>
                </div>
                {details.metadata?.author && (
                  <div className="text-sm text-gray-500 font-medium mb-4">Published by <span className={`${t.text600}`}>{details.metadata.author}</span></div>
                )}
                {/* Summary */}
                <div>
                  <h3 className="text-lg font-bold text-gray-800 mb-3">Summary</h3>
                  <div className="text-base text-gray-700 max-w-lg bg-gray-50 rounded-xl px-6 py-5 mb-2 shadow-sm border border-gray-100">
                    {details.metadata?.summary || <span className="text-gray-400">No summary provided.</span>}
                  </div>
                </div>
                {/* Tags */}
                {details.metadata?.tags && details.metadata.tags.length > 0 && (
                  <div className="flex flex-wrap gap-3 mt-2">
                      {details.metadata.tags.map(tag => (
                      <span key={tag} className={`inline-block ${t.bg50} ${t.text600} px-3 py-1 rounded-full text-xs font-semibold border ${t.border600}`}>{tag}</span>
                      ))}
                  </div>
                )}
                {/* Meta Info */}
                <div className="flex flex-wrap gap-4 mt-4">
                  {details.metadata?.author && (
                    <div className="bg-gray-50 border border-gray-200 rounded-xl shadow-sm px-4 py-2 flex items-center">
                      <span className="text-xs text-gray-500 mr-2">Author:</span>
                      <span className={`font-semibold ${t.text600}`}>{details.metadata.author}</span>
                    </div>
                  )}
                  {details.metadata?.code_hash && (
                    <div className="bg-gray-50 border border-gray-200 rounded-xl shadow-sm px-4 py-2 flex items-center">
                      <span className="text-xs text-gray-500 mr-2">Code Hash:</span>
                      <span className={`font-mono text-xs ${t.text600} truncate`} title={details.metadata.code_hash}>{details.metadata.code_hash.slice(0, 8)}</span>
                  </div>
                )}
                </div>
                {/* Publish Button (if provider and not published) */}
                {profile === 'provider' && !details.published && (
                  <div className="flex justify-end mt-6">
                    <Button variant="primary" onClick={() => setShowPublishModal(true)}>
                      Publish Router
                    </Button>
                  </div>
                )}
              </div>
              {/* Right Column: Services Card */}
              <div className="w-full md:w-96 flex-shrink-0">
                {details.services && details.services.length > 0 && (
                  <div className={`bg-white border ${t.border600} rounded-2xl shadow-lg p-8 space-y-4`}>
                    {details.services.map((service) => (
                      <div
                        key={service.type}
                        className={`flex items-center justify-between text-base font-semibold px-2 py-2 rounded-md border ${service.enabled ? 'bg-blue-50 text-blue-700 border-blue-200' : 'bg-gray-50 text-gray-400 border-gray-200'}`}
                      >
                        <span className="capitalize">{service.type}</span>
                        <span className="font-mono">${service.pricing} {service.charge_type.replace('_', ' ')}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Documentation Tab */}
          {activeTab === 'documentation' && (
            <div className="space-y-8 mt-10">
              {/* Description Section */}
              <div className="bg-white rounded-xl shadow-sm border p-8">
                <h4 className="text-lg font-bold text-gray-700 mb-3">Description</h4>
                <div className="prose prose-base max-w-none" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(getMarkdownHtml(details.metadata?.description || '')) }} />
              </div>

              {/* API Endpoints Section */}
              {details.endpoints && Object.keys(details.endpoints).length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-8">
                  <h4 className="text-lg font-bold text-gray-700 mb-6">API Endpoints</h4>
                  <div className="space-y-6">
                    {Object.entries(details.endpoints).map(([endpointName, endpointData]) => {
                      const endpoint = endpointData as EndpointInfo;
                      return (
                        <div key={endpointName} className="border border-gray-200 rounded-lg p-6">
                          <div className="flex items-center gap-3 mb-4">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                              endpoint.method === 'POST' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {endpoint.method}
                            </span>
                            <code className="text-lg font-mono text-gray-800 bg-gray-100 px-3 py-1 rounded">
                              {endpoint.path}
                            </code>
                            <span className="text-lg font-semibold text-gray-700 capitalize">
                              {endpointName}
                            </span>
                          </div>
                          
                          <p className="text-gray-600 mb-4">{endpoint.description}</p>
                          
                          {/* Parameters */}
                          {endpoint.parameters && Object.keys(endpoint.parameters).length > 0 && (
                            <div className="mb-4">
                              <h5 className="text-sm font-semibold text-gray-700 mb-2">Parameters:</h5>
                              <div className="bg-gray-50 rounded-lg p-4">
                                {Object.entries(endpoint.parameters).map(([paramName, paramType]) => (
                                  <div key={paramName} className="flex justify-between items-center py-1">
                                    <code className="text-sm font-mono text-blue-600">{paramName}</code>
                                    <span className="text-sm text-gray-600">{paramType}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Response */}
                          {endpoint.response && (
                            <div>
                              <h5 className="text-sm font-semibold text-gray-700 mb-2">Response:</h5>
                              <div className="bg-gray-50 rounded-lg p-4">
                                <code className="text-sm font-mono text-green-600">{endpoint.response}</code>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
      {/* Publish Router Modal */}
      {showPublishModal && details && (
        <PublishRouterModal
          isOpen={showPublishModal}
          onClose={() => {
            setShowPublishModal(false);
            setLoading(true);
            routerService.getUsername().then(usernameResp => {
              if (usernameResp.success && usernameResp.data) {
                return routerService.getRouterDetails(routerName, usernameResp.data.username, false);
              } else {
                throw new Error('Failed to get username');
              }
            }).then((resp) => {
              if (resp.success && resp.data) setDetails(resp.data);
              setLoading(false);
            });
          }}
          routerName={details.name}
        />
      )}
    </div>
  );
} 