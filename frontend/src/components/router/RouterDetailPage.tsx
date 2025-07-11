
import { useEffect, useState } from 'preact/hooks';
import { routerService } from '../../services/routerService';
import { Button } from '../shared/Button';
import type { ProfileType } from '../shared/ProfileToggle';
import { useTheme, themeClass } from '../shared/ThemeContext';
import { PublishRouterModal } from './PublishRouterModal';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import type { RouterDetails as RouterDetailsType, ServiceOverview, OpenAPISpecification, OpenAPIOperation } from '../../types/router';

interface RouterDetailProps {
  routerName: string;
  published: boolean;
  author: string;
  onBack: () => void;
  profile: ProfileType;
}

interface RouterDetails {
  name: string;
  published: boolean;
  services?: ServiceOverview[];
  metadata?: RouterDetailsType['metadata'];
  endpoints?: OpenAPISpecification;
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

// Utility to get method color
function getMethodColor(method: string): string {
  switch (method.toUpperCase()) {
    case 'GET':
      return 'bg-green-100 text-green-800 border-green-200';
    case 'POST':
      return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'PUT':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'DELETE':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'PATCH':
      return 'bg-purple-100 text-purple-800 border-purple-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
}

// Component to render OpenAPI schema
function SchemaRenderer({ schema, name }: { schema: any; name?: string }) {
  if (!schema || typeof schema !== 'object') return null;

  const renderSchemaType = (schema: any) => {
    if (schema.$ref) {
      const refName = schema.$ref.split('/').pop();
      return <span className="text-blue-600 font-mono">{refName}</span>;
    }
    
    if (schema.enum) {
      return (
        <div className="flex flex-wrap gap-1">
          {schema.enum.map((value: string) => (
            <span key={value} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
              {value}
            </span>
          ))}
        </div>
      );
    }
    
    if (schema.type === 'array' && schema.items) {
      return (
        <span className="text-gray-700">
          Array of <SchemaRenderer schema={schema.items} />
        </span>
      );
    }
    
    if (schema.type === 'object' && schema.properties) {
      return (
        <div className="ml-4 border-l-2 border-gray-200 pl-3">
          {Object.entries(schema.properties).map(([propName, propSchema]: [string, any]) => (
            <div key={propName} className="mb-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm text-gray-800">{propName}</span>
                {schema.required?.includes(propName) && (
                  <span className="text-xs bg-red-100 text-red-700 px-1 rounded">required</span>
                )}
              </div>
              <div className="ml-4">
                <SchemaRenderer schema={propSchema} />
              </div>
            </div>
          ))}
        </div>
      );
    }
    
    return <span className="text-gray-700 font-mono">{schema.type || 'object'}</span>;
  };

  return (
    <div className="text-sm">
      {name && <span className="font-semibold text-gray-800 mr-2">{name}:</span>}
      {renderSchemaType(schema)}
    </div>
  );
}

// Component to render OpenAPI operation
function OperationRenderer({ path, method, operation }: { path: string; method: string; operation: OpenAPIOperation }) {
  if (!operation || typeof operation !== 'object') return null;

  return (
    <div className="border border-gray-200 rounded-lg p-6 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${getMethodColor(method)}`}>
          {method.toUpperCase()}
        </span>
        <code className="text-lg font-mono text-gray-800 bg-gray-100 px-3 py-1 rounded">
          {path}
        </code>
        <span className="text-lg font-semibold text-gray-700">
          {operation.summary || 'No summary'}
        </span>
      </div>
      
      <p className="text-gray-600 mb-4 whitespace-pre-line">{operation.description || 'No description available'}</p>
      
      {/* Parameters */}
      {operation.parameters && Array.isArray(operation.parameters) && operation.parameters.length > 0 && (
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">Parameters:</h5>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            {operation.parameters.map((param) => (
              <div key={param.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <code className="text-sm font-mono text-blue-600">{param.name}</code>
                  <span className="text-xs text-gray-500">({param.in})</span>
                  {param.required && (
                    <span className="text-xs bg-red-100 text-red-700 px-1 rounded">required</span>
                  )}
                </div>
                <SchemaRenderer schema={param.schema} />
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Request Body */}
      {operation.requestBody && operation.requestBody.content && operation.requestBody.content['application/json'] && (
        <div className="mb-4">
          <h5 className="text-sm font-semibold text-gray-700 mb-2">Request Body:</h5>
          <div className="bg-gray-50 rounded-lg p-4">
            <SchemaRenderer schema={operation.requestBody.content['application/json'].schema} />
          </div>
        </div>
      )}
      
      {/* Responses */}
      <div>
        <h5 className="text-sm font-semibold text-gray-700 mb-2">Responses:</h5>
        <div className="space-y-2">
          {operation.responses && Object.entries(operation.responses).map(([statusCode, response]) => (
            <div key={statusCode} className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-semibold ${
                  statusCode.startsWith('2') ? 'bg-green-100 text-green-800' : 
                  statusCode.startsWith('4') ? 'bg-red-100 text-red-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {statusCode}
                </span>
                <span className="text-sm text-gray-600">{response.description || 'No description'}</span>
              </div>
              {response.content && response.content['application/json'] && (
                <SchemaRenderer schema={response.content['application/json'].schema} />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function RouterDetailPage({ routerName, published, author, onBack, profile }: RouterDetailProps) {
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
    routerService.getRouterDetails(routerName, author, published)
      .then((resp) => {
        if (resp.success && resp.data) {
          setDetails(resp.data);
        } else {
          setError(resp.error || 'Failed to load router details.');
        }
      })
      .catch(() => setError('Failed to load router details.'))
      .finally(() => setLoading(false));
  }, [routerName, author, published]);

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
            <button className={`px-4 py-2 text-base font-semibold border-b-2 transition-colors duration-200 ${activeTab === 'documentation' ? t.border600 + ' ' + t.text600 : 'border-transparent text-gray-400'} bg-white focus:outline-none`} onClick={() => setActiveTab('documentation')}>API Documentation</button>
            <button className="px-4 py-2 text-base font-semibold text-gray-400 cursor-not-allowed flex items-center gap-2" disabled>
              Usage
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 border border-yellow-200 ml-2">Coming Soon</span>
            </button>
          </div>

          {activeTab === 'overview' && details && (
            <div className="flex flex-col md:flex-row gap-12">
              {/* Left Column: Summary, Tags, Meta */}
              <div className="flex-1 space-y-8">
                {/* Header */}
                <div className="flex items-center gap-3 mb-2">
                  <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">{formatRouterName(details.name)}</h2>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${details.published ? t.bg50 + ' ' + t.text600 : 'bg-gray-100 text-gray-800'} border ${details.published ? t.border600 : 'border-gray-200'}`}>{details.published ? 'Published' : 'Draft'}</span>
                </div>
                {details.metadata?.author && (
                  <div className="mb-4">
                    <span className="inline-flex items-center px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full font-medium text-sm gap-2">
                      <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 15c2.485 0 4.797.755 6.879 2.047M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <a
                        href={`mailto:${details.metadata.author}`}
                        className="hover:underline font-semibold"
                      >
                        {details.metadata.author}
                      </a>
                    </span>
                  </div>
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
              <div className="w-full md:w-96 flex-shrink-0 space-y-4">
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
                {/* Code Hash Card (moved here) */}
                {details.metadata?.code_hash && (
                  <div className="bg-gray-50 border border-gray-200 rounded-xl shadow-sm px-4 py-2 flex items-center">
                    <span className="text-xs text-gray-500 mr-2">Code Hash:</span>
                    <span className={`font-mono text-xs ${t.text600} truncate`} title={details.metadata.code_hash}>{details.metadata.code_hash.slice(0, 8)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* API Documentation Tab */}
          {activeTab === 'documentation' && (
            <div className="space-y-8 mt-10">
              {/* Description Section */}
              <div className="bg-white rounded-xl shadow-sm border p-8">
                <h4 className="text-lg font-bold text-gray-700 mb-3">Description</h4>
                <div className="prose prose-base max-w-none" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(getMarkdownHtml(details.metadata?.description || '')) }} />
              </div>

              {/* OpenAPI Documentation Section */}
              {details.endpoints && details.endpoints.info && details.endpoints.paths && (
                <div className="bg-white rounded-xl shadow-sm border p-8">
                  <div className="flex items-center justify-between mb-6">
                    <h4 className="text-lg font-bold text-gray-700">API Endpoints</h4>
                    <div className="text-sm text-gray-500">
                      OpenAPI {details.endpoints.openapi || 'Unknown'}
                    </div>
                  </div>
                  
                  {/* API Info */}
                  {details.endpoints.info && (
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                      <h5 className="font-semibold text-gray-800 mb-2">{details.endpoints.info.title || 'API Documentation'}</h5>
                      <p className="text-gray-600 text-sm">{details.endpoints.info.description || 'No description available'}</p>
                      <p className="text-gray-500 text-xs mt-1">Version: {details.endpoints.info.version || 'Unknown'}</p>
                    </div>
                  )}

                  {/* Endpoints */}
                  <div className="space-y-6">
                    {Object.entries(details.endpoints.paths).map(([path, methods]) => (
                      <div key={path}>
                        {Object.entries(methods).map(([method, operation]) => (
                          <OperationRenderer
                            key={`${method}-${path}`}
                            path={path}
                            method={method}
                            operation={operation}
                          />
                        ))}
                      </div>
                    ))}
                  </div>

                  {/* Schemas Section */}
                  {details.endpoints.components?.schemas && Object.keys(details.endpoints.components.schemas).length > 0 && (
                    <div className="mt-8">
                      <h5 className="text-lg font-bold text-gray-700 mb-4">Data Models</h5>
                      <div className="space-y-4">
                        {Object.entries(details.endpoints.components.schemas).map(([schemaName, schema]) => (
                          <div key={schemaName} className="border border-gray-200 rounded-lg p-4">
                            <h6 className="font-semibold text-gray-800 mb-2">{schemaName}</h6>
                            {schema.description && (
                              <p className="text-gray-600 text-sm mb-3">{schema.description}</p>
                            )}
                            <SchemaRenderer schema={schema} />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {/* Fallback for when endpoints are not available */}
              {!details.endpoints && (
                <div className="bg-white rounded-xl shadow-sm border p-8">
                  <h4 className="text-lg font-bold text-gray-700 mb-4">API Documentation</h4>
                  <p className="text-gray-500">No API documentation available for this router.</p>
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
          onClose={() => setShowPublishModal(false)}
          routerName={details.name}
          onSuccess={() => {
            setShowPublishModal(false);
            // Refresh the page to show updated published status
            window.location.reload();
          }}
        />
      )}
    </div>
  );
} 