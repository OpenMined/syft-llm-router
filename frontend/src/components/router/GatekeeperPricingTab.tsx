import { useState, useEffect } from 'preact/hooks';
import { routerService } from '../../services/routerService';
import { Button } from '../shared/Button';
import { GATEKEEPER_TERM } from '../../utils/constants';
import type { ServiceOverview, PricingChargeType } from '../../types/router';

interface GatekeeperPricingTabProps {
  routerName: string;
  author: string;
  services: ServiceOverview[];
}

export function GatekeeperPricingTab({ routerName, author, services: initialServices }: GatekeeperPricingTabProps) {
  const [services, setServices] = useState<ServiceOverview[]>(initialServices);
  const [editedServices, setEditedServices] = useState<ServiceOverview[]>(initialServices);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [syftboxUrl, setSyftboxUrl] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string>('Pricing updated successfully!');

  useEffect(() => {
    setServices(initialServices);
    setEditedServices(initialServices);
    setSuccess(false);
    setSuccessMessage('Pricing updated successfully!');
  }, [initialServices]);

  useEffect(() => {
    // Fetch SyftBox URL for API calls
    routerService.getSyftBoxUrl().then(resp => {
      if (resp.success && resp.data) {
        setSyftboxUrl(resp.data.url);
      }
    });
  }, []);

  useEffect(() => {
    // Check if there are any changes
    const changed = JSON.stringify(services) !== JSON.stringify(editedServices);
    setHasChanges(changed);
  }, [services, editedServices]);

  const handlePricingChange = (serviceType: string, newPrice: string) => {
    const updatedServices = editedServices.map(service => {
      if (service.type === serviceType) {
        return {
          ...service,
          pricing: parseFloat(newPrice) || 0
        };
      }
      return service;
    });
    setEditedServices(updatedServices);
    setError(null);
    setSuccess(false);
    setSuccessMessage('Pricing updated successfully!');
  };

  const handleSave = async () => {
    if (!syftboxUrl) {
      setError('SyftBox URL not available');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(false);
    setSuccessMessage('Pricing updated successfully!');

    try {
      const response = await routerService.updateGatekeeperControl(
        syftboxUrl,
        author,
        routerName,
        editedServices
      );

      if (response.success) {
        // Check if this is an async request (polling response)
        if (response.data && response.data.isAsync) {
          setSuccess(true);
          setSuccessMessage(`Request submitted to ${routerName} router, please check after some time.`);
          // Don't update services immediately for async requests
          // The message will indicate the request is being processed
        } else {
          setSuccess(true);
          setSuccessMessage('Pricing updated successfully!');
          setServices(editedServices);
        }
        setTimeout(() => setSuccess(false), 5000); // Longer timeout for async messages
      } else {
        setError(response.error || 'Failed to update pricing');
      }
    } catch (err) {
      setError('Error updating pricing');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setEditedServices(services);
    setError(null);
    setSuccess(false);
    setSuccessMessage('Pricing updated successfully!');
  };

  const getServiceIcon = (serviceType: string) => {
    switch (serviceType) {
      case 'chat':
        return (
          <svg className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        );
      case 'search':
        return (
          <svg className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        );
      default:
        return (
          <svg className="h-5 w-5 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-bold text-gray-800">{GATEKEEPER_TERM} Pricing Control</h3>
        <p className="text-sm text-gray-600 mt-1">
          Manage pricing for router services as an authorized {GATEKEEPER_TERM}
        </p>
      </div>

      {/* Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <svg className="h-5 w-5 text-blue-600 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="text-sm text-blue-800">
            <p className="font-medium">You are managing this router as a {GATEKEEPER_TERM}</p>
            <p className="mt-1">You have permission to update service pricing. Service availability is managed by the router owner.</p>
          </div>
        </div>
      </div>

      {/* Services Pricing */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-4">Service Pricing</h4>
          
          {editedServices.length === 0 ? (
            <p className="text-gray-500">No services configured for this router</p>
          ) : (
            <div className="space-y-4">
              {editedServices.map((service) => (
                <div key={service.type} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    {getServiceIcon(service.type)}
                    <span className="font-medium text-gray-900 capitalize">
                      {service.type} Service
                    </span>
                    {!service.enabled && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                        Disabled
                      </span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Price ($)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={service.pricing}
                        onChange={(e) => handlePricingChange(service.type, (e.target as HTMLInputElement).value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">
                        Charge Type
                      </label>
                      <div className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-gray-600">
                        {service.charge_type.replace('_', ' ')}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
          {error}
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
          {successMessage}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <Button
          variant="ghost"
          onClick={handleReset}
          disabled={!hasChanges || saving}
        >
          Reset Changes
        </Button>
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={!hasChanges || saving || !syftboxUrl}
        >
          {saving ? 'Saving...' : 'Save Pricing'}
        </Button>
      </div>
    </div>
  );
}