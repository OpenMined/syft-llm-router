import { h } from 'preact';
import { useState } from 'preact/hooks';
import { Modal } from '../shared/Modal';
import { Button } from '../shared/Button';
import { useTheme, themeClass } from '../shared/ThemeContext';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { routerService } from '../../services/routerService';
import { RouterServiceType, PricingChargeType, type ServiceOverview } from '../../types/router';

// @ts-ignore
// eslint-disable-next-line

interface PublishRouterModalProps {
  isOpen: boolean;
  onClose: () => void;
  routerName: string;
  onSuccess?: (publishedPath: string) => void;
}

type Step = 1 | 2 | 3 | 4 | 5 | 6 | 7;

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

// Define a local type for modal state
interface ModalServiceOverview {
  type: RouterServiceType;
  pricing: string;
  charge_type: PricingChargeType;
  enabled: boolean;
}

const ALL_SERVICES: ModalServiceOverview[] = [
  {
    type: RouterServiceType.CHAT,
    pricing: '0',
    charge_type: PricingChargeType.PER_REQUEST,
    enabled: false,
  },
  {
    type: RouterServiceType.SEARCH,
    pricing: '0',
    charge_type: PricingChargeType.PER_REQUEST,
    enabled: false,
  },
];

export function PublishRouterModal({ isOpen, onClose, routerName, onSuccess }: PublishRouterModalProps) {
  const { color } = useTheme();
  const t = themeClass(color);
  const [step, setStep] = useState<Step>(1);
  const [summary, setSummary] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [services, setServices] = useState<ModalServiceOverview[]>(ALL_SERVICES);
  const [publishedPath, setPublishedPath] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [descriptionError, setDescriptionError] = useState<string | null>(null);

  // Stepper
  const stepLabels = ['Router Name', 'Summary', 'Description', 'Tags', 'Pricing', 'Review', 'Success'];
  const renderStepper = () => (
    <div className="flex flex-col items-center mb-8">
      <div className="flex items-center w-full max-w-lg">
        {stepLabels.map((label, idx) => {
          const isActive = step === idx + 1;
          const isCompleted = step > idx + 1;
          return (
            <div key={label} className="flex-1 flex flex-col items-center">
              <div className="relative flex items-center justify-center">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors duration-200
                    ${isCompleted ? `${t.bg600} ${t.border600} text-white` : isActive ? `bg-white ${t.border600} ${t.text600}` : 'bg-gray-200 border-gray-300 text-gray-400'}`}
                >
                  {isCompleted ? (
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <span className="font-bold">{idx + 1}</span>
                  )}
                </div>
                {idx < stepLabels.length - 1 && (
                  <div className={`absolute left-full top-1/2 transform -translate-y-1/2 w-12 h-1 ${step > idx + 1 ? t.bg600 : 'bg-gray-300'}`}></div>
                )}
              </div>
              <span className={`mt-2 text-xs font-medium ${isActive ? t.text700 : isCompleted ? t.text600 : 'text-gray-400'}`}>{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Step content
  let content: h.JSX.Element = <div />;
  if (step === 1) {
    content = (
      <div>
        {renderStepper()}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Router Name</label>
          <input type="text" value={routerName} disabled className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-700" />
        </div>
        <div className="flex justify-end">
          <Button variant="primary" onClick={() => setStep(2)}>Next</Button>
        </div>
      </div>
    );
  } else if (step === 2) {
    content = (
      <div>
        {renderStepper()}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Summary (max 100 words)</label>
          <textarea
            value={summary}
            onInput={e => {
              setSummary((e.target as HTMLTextAreaElement).value);
              if ((e.target as HTMLTextAreaElement).value.trim()) setSummaryError(null);
            }}
            maxLength={800}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter a short summary of your router..."
          />
          {summaryError && <div className="text-error-600 text-xs mt-1">{summaryError}</div>}
        </div>
        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
          <Button variant="primary" onClick={() => { if (validateStep()) setStep(3); }} disabled={!summary.trim()}>Next</Button>
        </div>
      </div>
    );
  } else if (step === 3) {
    content = (
      <div>
        {renderStepper()}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Description (Markdown supported)</label>
          <textarea
            value={description}
            onInput={e => {
              setDescription((e.target as HTMLTextAreaElement).value);
              if ((e.target as HTMLTextAreaElement).value.trim()) setDescriptionError(null);
            }}
            maxLength={800}
            rows={8}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-4"
            placeholder="Write your router description using markdown..."
          />
          {descriptionError && <div className="text-error-600 text-xs mt-1">{descriptionError}</div>}
          <div className="mt-2">
            <label className="block text-xs font-medium text-gray-500 mb-1">Preview:</label>
            <div className="prose prose-sm max-w-none border rounded p-3 bg-gray-50" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(getMarkdownHtml(description)) }} />
          </div>
        </div>
        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep(2)}>Back</Button>
          <Button variant="primary" onClick={() => { if (validateStep()) setStep(4); }} disabled={!description.trim()}>Next</Button>
        </div>
      </div>
    );
  } else if (step === 4) {
    content = (
      <div>
        {renderStepper()}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
          <div className="flex items-center gap-2 mb-2">
            <input
              type="text"
              value={tagInput}
              onInput={e => setTagInput((e.target as HTMLInputElement).value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Add a tag..."
              onKeyDown={e => {
                if (e.key === 'Enter' && tagInput.trim()) {
                  setTags([...tags, tagInput.trim()]);
                  setTagInput('');
                  e.preventDefault();
                }
              }}
            />
            <Button variant="primary" size="sm" onClick={() => { if (tagInput.trim()) { setTags([...tags, tagInput.trim()]); setTagInput(''); } }}>+
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, idx) => (
              <span key={tag + idx} className="inline-flex items-center px-2 py-0.5 rounded bg-gray-200 text-gray-700 text-xs font-medium">
                {tag}
                <button className="ml-1 text-gray-500 hover:text-red-500" onClick={() => setTags(tags.filter((_, i) => i !== idx))}>&times;</button>
              </span>
            ))}
          </div>
        </div>
        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep(3)}>Back</Button>
          <Button variant="primary" onClick={() => setStep(5)}>Next</Button>
        </div>
      </div>
    );
  } else if (step === 5) {
    content = (
      <div>
        {renderStepper()}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Pricing (USD)</label>
          <div className="space-y-4">
            {services.map((service) => (
              <div
                key={service.type}
                className={`flex items-center gap-4 p-4 rounded-lg border ${service.enabled ? 'bg-blue-50 border-blue-200' : 'bg-gray-50 border-gray-200'} shadow-sm transition`}
              >
                <label className="flex items-center gap-2 font-semibold text-lg cursor-pointer">
                  <span className={service.enabled ? 'text-blue-700' : 'text-gray-400'}>{service.type}</span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={service.enabled}
                    tabIndex={0}
                    onClick={() => handleServiceToggle(service.type)}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') handleServiceToggle(service.type); }}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none ${service.enabled ? t.bg600 : 'bg-gray-300'}`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200 ${service.enabled ? 'translate-x-5' : 'translate-x-1'}`}
                    />
                  </button>
                </label>
                <div className="flex items-center gap-1">
                  <span className="text-gray-500">$</span>
              <input
                    type="text"
                    value={service.pricing}
                    onInput={e => handleServicePrice(service.type, (e.target as HTMLInputElement).value)}
                    disabled={!service.enabled}
                    className="w-20 px-2 py-1 rounded border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-200 disabled:bg-gray-100"
                    placeholder="$ per request"
                  />
            </div>
                <select
                  value={service.charge_type}
                  onChange={e => handleServiceChargeType(service.type, e)}
                  disabled={!service.enabled}
                  className="px-2 py-1 rounded border border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-200 disabled:bg-gray-100"
                >
                  <option value={PricingChargeType.PER_REQUEST}>per request</option>
                  {/* Add more charge types here if needed */}
                </select>
            </div>
            ))}
          </div>
        </div>
        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep(4)}>Back</Button>
          <Button variant="primary" onClick={() => { if (validateStep()) setStep(6); }} disabled={!services.some(s => s.enabled)}>Review</Button>
        </div>
      </div>
    );
  } else if (step === 6) {
    content = (
      <div>
        {renderStepper()}
        {error && <div className="bg-error-50 border border-error-200 rounded-md p-4 text-error-700 text-sm mb-4">{error}</div>}
        <div className="mb-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Router Name</label>
            <div className="p-2 bg-gray-50 rounded border text-gray-700">{routerName}</div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Summary</label>
            <div className="p-2 bg-gray-50 rounded border text-gray-700">{summary}</div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
            <div className="prose prose-sm max-w-none border rounded p-3 bg-gray-50" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(getMarkdownHtml(description)) }} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Tags</label>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, idx) => (
                <span key={tag + idx} className="inline-flex items-center px-2 py-0.5 rounded bg-gray-200 text-gray-700 text-xs font-medium">{tag}</span>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Pricing</label>
            <div className="flex gap-4">
              {services.map(service => (
                <div key={service.type} className="flex-1">
                  <span className="font-mono">{service.type}: ${service.pricing || '0.00'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-between">
          <Button variant="ghost" onClick={() => setStep(5)} disabled={loading}>Back</Button>
          <Button variant="primary" onClick={async () => {
            setLoading(true);
            setError(null);
            const req = {
              router_name: routerName,
              summary,
              description,
              tags,
              services: services.map(service => ({ ...service, pricing: parseFloat(service.pricing) })),
            };
            const resp = await routerService.publishRouter(req);
            setLoading(false);
            if (resp.success && resp.data && resp.data.published_path) {
              setPublishedPath(resp.data.published_path);
              setStep(7);
              if (onSuccess) onSuccess(resp.data.published_path);
            } else {
              setError(resp.error || 'Failed to publish router');
            }
          }} loading={loading} disabled={loading || !services.some(s => s.enabled)}>Publish</Button>
        </div>
      </div>
    );
  } else if (step === 7) {
    content = (
      <div>
        {renderStepper()}
        <div className="text-center py-8">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success-100 mb-4">
            <svg className="h-6 w-6 text-success-600 animate-checkmark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Router Published!</h3>
          <p className="text-sm text-gray-500 mb-4">Your router has been published successfully.</p>
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">Published Path:</p>
            <div className="flex items-center justify-between bg-white rounded border p-2">
              <code className="text-sm text-gray-600 flex-1 mr-2 truncate">{publishedPath || '/path/to/published/router'}</code>
            </div>
          </div>
          <div className="flex justify-center space-x-3">
            <Button variant="primary" onClick={onClose}>Go to Routers</Button>
          </div>
        </div>
      </div>
    );
  }

  function validateStep() {
    let valid = true;
    if (step === 2) {
      if (!summary.trim()) {
        setSummaryError('Summary is required');
        valid = false;
      } else {
        setSummaryError(null);
      }
    }
    if (step === 3) {
      if (!description.trim()) {
        setDescriptionError('Description is required');
        valid = false;
      } else {
        setDescriptionError(null);
      }
    }
    // Do NOT require tags for step 4
    return valid;
  }

  // Service enable/disable, price, and charge type handlers
  const handleServiceToggle = (type: RouterServiceType) => {
    setServices(prev => prev.map(s =>
      s.type === type ? { ...s, enabled: !s.enabled, pricing: !s.enabled ? '0' : '0' } : s
    ));
  };
  const handleServicePrice = (type: RouterServiceType, value: string) => {
    setServices(prev => prev.map(s =>
      s.type === type ? { ...s, pricing: value } : s
    ));
  };
  const handleServiceChargeType = (type: RouterServiceType, e: Event) => {
    const value = (e.target as HTMLSelectElement).value as PricingChargeType;
    setServices(prev => prev.map(s =>
      s.type === type ? { ...s, charge_type: value } : s
    ));
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Publish Router" size="lg">
      {content}
    </Modal>
  );
} 