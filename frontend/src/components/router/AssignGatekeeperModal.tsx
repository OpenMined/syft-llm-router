import { useState, useEffect } from 'preact/hooks';
import { Modal } from '../shared/Modal';
import { Button } from '../shared/Button';
import { routerService } from '../../services/routerService';
import { GATEKEEPER_TERM } from '../../utils/constants';
import { delegateStatusService } from '../../services/delegateStatusService';
import type { AvailableDelegatesResponse } from '../../types/router';

interface AssignGatekeeperModalProps {
  isOpen: boolean;
  onClose: () => void;
  routerName: string;
  currentDelegate?: string; // Current delegate email if changing
  onSuccess: () => void;
}

export function AssignGatekeeperModal({ isOpen, onClose, routerName, currentDelegate, onSuccess }: AssignGatekeeperModalProps) {
  const [gatekeepers, setGatekeepers] = useState<string[]>([]);
  const [selectedGatekeeper, setSelectedGatekeeper] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchGatekeepers();
      // Reset state when modal opens
      setSelectedGatekeeper(currentDelegate || '');
      setError(null);
      setSuccess(false);
    }
  }, [isOpen, currentDelegate]);

  const fetchGatekeepers = async () => {
    setLoading(true);
    try {
      const response = await routerService.listGatekeepers();
      if (response.success && response.data) {
        setGatekeepers(response.data.delegates);
      } else {
        setError('Failed to load available gatekeepers');
      }
    } catch (err) {
      setError('Error fetching gatekeepers');
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorize = async () => {
    if (!selectedGatekeeper) {
      setError('Please select a gatekeeper');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const response = await routerService.grantGatekeeper({
        router_name: routerName,
        delegate_email: selectedGatekeeper
      });

      if (response.success) {
        setSuccess(true);
        // Refresh delegate status cache since delegation assignments may have changed
        delegateStatusService.refreshStatus();
        setTimeout(() => {
          onSuccess();
        }, 1500);
      } else {
        setError(response.error || 'Failed to assign gatekeeper');
      }
    } catch (err) {
      setError('Error assigning gatekeeper');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async () => {
    if (!confirm(`Are you sure you want to revoke ${GATEKEEPER_TERM} access for this router?`)) {
      return;
    }

    setRevoking(true);
    setError(null);

    try {
      const response = await routerService.revokeGatekeeper({
        router_name: routerName
      });

      if (response.success) {
        setSuccess(true);
        // Refresh delegate status cache
        delegateStatusService.refreshStatus();
        setTimeout(() => {
          onSuccess();
        }, 1500);
      } else {
        setError(response.error || 'Failed to revoke gatekeeper');
      }
    } catch (err) {
      setError('Error revoking gatekeeper');
    } finally {
      setRevoking(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Assign ${GATEKEEPER_TERM}`}
      size="md"
    >
      <div className="space-y-4">
        {/* Router Name (read-only) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Router Name
          </label>
          <input
            type="text"
            value={routerName}
            disabled
            className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md text-gray-600 cursor-not-allowed"
          />
        </div>

        {/* Gatekeeper Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select {GATEKEEPER_TERM}
          </label>
          {loading ? (
            <div className="text-sm text-gray-500">Loading available gatekeepers...</div>
          ) : gatekeepers.length === 0 ? (
            <div className="text-sm text-gray-500">No gatekeepers available</div>
          ) : (
            <select
              value={selectedGatekeeper}
              onChange={(e) => setSelectedGatekeeper((e.target as HTMLSelectElement).value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={submitting}
            >
              <option value="">Choose a gatekeeper...</option>
              {gatekeepers.map((gatekeeperEmail) => (
                <option key={gatekeeperEmail} value={gatekeeperEmail}>
                  {gatekeeperEmail}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Control Type (fixed) */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Control Type
          </label>
          <div className="flex items-center px-3 py-2 bg-blue-50 border border-blue-200 rounded-md">
            <svg className="h-4 w-4 text-blue-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
            </svg>
            <span className="text-sm font-medium text-blue-700">Pricing Update</span>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md text-sm">
            {GATEKEEPER_TERM} successfully {currentDelegate ? 'changed' : 'assigned'}! Redirecting...
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-between pt-4">
          {/* Left side - Revoke button for existing delegates */}
          <div>
            {currentDelegate && !success && (
              <Button
                variant="ghost"
                onClick={handleRevoke}
                disabled={revoking || submitting}
                className="text-red-600 hover:text-red-800 hover:bg-red-50"
              >
                {revoking ? 'Revoking...' : `Remove ${GATEKEEPER_TERM}`}
              </Button>
            )}
          </div>
          
          {/* Right side - Main actions */}
          <div className="flex gap-3">
            <Button
              variant="ghost"
              onClick={onClose}
              disabled={submitting || revoking}
            >
              Cancel
            </Button>
            {!success && (
              <Button
                variant="primary"
                onClick={handleAuthorize}
                disabled={submitting || revoking || loading || !selectedGatekeeper || selectedGatekeeper === currentDelegate}
              >
                {submitting ? 'Updating...' : currentDelegate ? `Change ${GATEKEEPER_TERM}` : 'Authorize'}
              </Button>
            )}
            {success && (
              <Button
                variant="secondary"
                onClick={() => window.location.reload()}
              >
                Go to Router
              </Button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}