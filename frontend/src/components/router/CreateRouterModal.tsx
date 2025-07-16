import { h } from 'preact';
import { useState } from 'preact/hooks';
import { Modal } from '../shared/Modal';
import { Button } from '../shared/Button';
import { routerService } from '../../services/routerService';
import { copyToClipboard } from '../../utils/clipboard';
import { RouterType, RouterServiceType, type CreateRouterRequest } from '../../types/router';
import { useTheme, themeClass } from '../shared/ThemeContext';

interface CreateRouterModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

type Step = 1 | 2 | 3 | 4;

export function CreateRouterModal({ isOpen, onClose, onSuccess }: CreateRouterModalProps) {
  const [step, setStep] = useState<Step>(1);
  const [formData, setFormData] = useState<CreateRouterRequest>({
    name: '',
    router_type: RouterType.DEFAULT,
    services: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ routerName: string; outputDir: string } | null>(null);

  const { color } = useTheme();
  const t = themeClass(color);

  // Step validation
  const validateStep = () => {
    if (step === 1 && !formData.name.trim()) {
      setError('Project name is required');
      return false;
    }
    if (step === 3 && formData.services.length === 0) {
      setError('Please select at least one service type');
      return false;
    }
    setError(null);
    return true;
  };

  // Step navigation
  const handleNext = async (e?: Event) => {
    if (e) e.preventDefault();
    if (!validateStep()) return;
    if (step === 3) {
      // Submit on last form step
      setLoading(true);
      try {
        const response = await routerService.createRouter(formData);
        if (response.success && response.data) {
          setSuccess({
            routerName: response.data.router_name,
            outputDir: response.data.output_dir
          });
          setStep(4);
        } else {
          setError(response.error || 'Failed to create router');
        }
      } catch (err) {
        setError('An unexpected error occurred');
      } finally {
        setLoading(false);
      }
    } else {
      setStep((s) => (s + 1) as Step);
    }
  };
  const handleBack = () => {
    if (step > 1) setStep((s) => (s - 1) as Step);
  };

  // Service toggle
  const handleServiceToggle = (service: RouterServiceType) => {
    setFormData(prev => ({
      ...prev,
      services: prev.services.includes(service)
        ? prev.services.filter(s => s !== service)
        : [...prev.services, service]
    }));
  };



  // Reset modal state
  const handleClose = () => {
    setFormData({ name: '', router_type: RouterType.DEFAULT, services: [] });
    setError(null);
    setSuccess(null);
    setStep(1);
    onClose();
  };

  // Manual trigger after success
  const handleSuccessDone = () => {
    handleClose();
    onSuccess(); // Now refresh the list only after user clicks CTA
  };

  // Enhanced Progress Stepper
  const stepLabels = ['Project Name', 'Router Type', 'Router Services', 'Success'];
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
      <form onSubmit={handleNext} className="space-y-6">
        {renderStepper()}
        {error && <div className="bg-error-50 border border-error-200 rounded-md p-4 text-error-700 text-sm">{error}</div>}
        <div>
          <label htmlFor="project-name" className="block text-sm font-medium text-gray-700 mb-2">Project Name *</label>
          <input
            type="text"
            id="project-name"
            value={formData.name}
            onInput={(e) => setFormData(prev => ({ ...prev, name: (e.target as HTMLInputElement).value }))}
            className={`w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none ${t.focusRing} focus:border-${color}-500`}
            placeholder="Enter project name"
            required
            autoFocus
          />
        </div>
        <div className="flex justify-between pt-4">
          <span />
          <Button type="submit" variant="primary">Next</Button>
        </div>
      </form>
    );
  } else if (step === 2) {
    content = (
      <form onSubmit={handleNext} className="space-y-6">
        {renderStepper()}
        {error && <div className="bg-error-50 border border-error-200 rounded-md p-4 text-error-700 text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Router Type *</label>
          <div className="space-y-2">
            {Object.values(RouterType).map((type) => (
              <label key={type} className="flex items-center">
                <input
                  type="radio"
                  name="router-type"
                  value={type}
                  checked={formData.router_type === type}
                  onChange={() => setFormData(prev => ({ ...prev, router_type: type }))}
                  className={`h-4 w-4 ${t.text600} ${t.focusRing} border-gray-300`}
                />
                <span className="ml-2 text-sm text-gray-700 capitalize">{type}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="flex justify-between pt-4">
          <Button type="button" variant="ghost" onClick={handleBack}>Back</Button>
          <Button type="submit" variant="primary">Next</Button>
        </div>
      </form>
    );
  } else if (step === 3) {
    content = (
      <form onSubmit={handleNext} className="space-y-6">
        {renderStepper()}
        {error && <div className="bg-error-50 border border-error-200 rounded-md p-4 text-error-700 text-sm">{error}</div>}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Router Services * (Select at least one)</label>
          <div className="space-y-2">
            {Object.values(RouterServiceType).map((service) => (
              <label key={service} className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.services.includes(service)}
                  onChange={() => handleServiceToggle(service)}
                  className={`h-4 w-4 ${t.text600} ${t.focusRing} border-gray-300 rounded`}
                />
                <span className="ml-2 text-sm text-gray-700 uppercase">{service}</span>
              </label>
            ))}
          </div>
        </div>
        <div className="flex justify-between pt-4">
          <Button type="button" variant="ghost" onClick={handleBack} disabled={loading}>Back</Button>
          <Button type="submit" variant="primary" loading={loading} disabled={loading}>Create Router</Button>
        </div>
      </form>
    );
  } else if (step === 4 && success) {
    content = (
      <div className="text-center">
        {renderStepper()}
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-success-100 mb-4">
          <svg className="h-6 w-6 text-success-600 animate-checkmark" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Router "{success.routerName}" Created!</h3>
        <p className="text-sm text-gray-500 mb-4">Your router has been successfully created and is ready for use.</p>
        <div className="bg-gray-50 rounded-lg p-4 mb-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Project Directory:</p>
          <div className="flex items-center justify-between bg-white rounded border p-2 mb-2">
            <code className="text-sm text-gray-600 flex-1 mr-2 truncate">{success.outputDir}</code>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => copyToClipboard(success.outputDir)}
              data-copy-button
              className="flex-shrink-0"
            >
              Copy
            </Button>
          </div>

        </div>
        <div className="flex justify-center space-x-3">
          <Button variant="primary" onClick={handleSuccessDone}>Go to Routers</Button>
        </div>
      </div>
    );
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Router" size="lg">
      {content}
    </Modal>
  );
} 