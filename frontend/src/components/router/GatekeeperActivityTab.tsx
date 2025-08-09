import { useState, useEffect } from 'preact/hooks';
import { routerService } from '../../services/routerService';
import { Button } from '../shared/Button';
import { GATEKEEPER_TERM } from '../../utils/constants';
import type { DCALogsResponse } from '../../types/router';

interface GatekeeperActivityTabProps {
  routerName: string;
  onRevoke: () => void;
}

export function GatekeeperActivityTab({ routerName, onRevoke }: GatekeeperActivityTabProps) {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [revoking, setRevoking] = useState(false);

  useEffect(() => {
    fetchLogs();
  }, [routerName]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await routerService.getGatekeeperLogs(routerName);
      if (response.success && response.data) {
        setLogs(response.data.audit_logs || []);
      } else {
        setError('Failed to load activity logs');
      }
    } catch (err) {
      setError('Error fetching activity logs');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async () => {
    if (!confirm(`Are you sure you want to revoke ${GATEKEEPER_TERM} access for this router?`)) {
      return;
    }

    setRevoking(true);
    try {
      const response = await routerService.revokeGatekeeper({
        router_name: routerName
      });

      if (response.success) {
        onRevoke();
      } else {
        alert(`Failed to revoke ${GATEKEEPER_TERM}: ${response.error}`);
      }
    } catch (err) {
      alert(`Error revoking ${GATEKEEPER_TERM}`);
    } finally {
      setRevoking(false);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getActionIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'grant':
      case 'assigned':
        return (
          <svg className="h-4 w-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'revoke':
      case 'removed':
        return (
          <svg className="h-4 w-4 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'update_pricing':
      case 'pricing_update':
      case 'price_change':
        return (
          <svg className="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
        );
      default:
        return (
          <svg className="h-4 w-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Revoke Button */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-bold text-gray-800">{GATEKEEPER_TERM} Activity</h3>
          <p className="text-sm text-gray-600 mt-1">
            View all activities performed by the assigned {GATEKEEPER_TERM}
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={handleRevoke}
          disabled={revoking}
          className="text-red-600 hover:text-red-800 hover:bg-red-50"
        >
          {revoking ? 'Revoking...' : `Revoke ${GATEKEEPER_TERM}`}
        </Button>
      </div>

      {/* Activity Logs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {loading ? (
          <div className="py-12 text-center text-gray-500">Loading activity logs...</div>
        ) : error ? (
          <div className="py-12 text-center text-red-600">{error}</div>
        ) : logs.length === 0 ? (
          <div className="py-12 text-center text-gray-500">No activity logs available</div>
        ) : (
          <div className="divide-y divide-gray-200">
            {logs.map((log, index) => (
              <div key={index} className="p-4 hover:bg-gray-50">
                <div className="flex items-start gap-3">
                  <div className="mt-1">
                    {getActionIcon(log.control_type)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-gray-900 capitalize">
                        {log.control_type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(log.created_at)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      {GATEKEEPER_TERM}: <span className="font-medium">{log.delegate_email}</span>
                    </div>
                    {log.reason && (
                      <div className="text-sm text-gray-600 mt-1">
                        Reason: <span className="italic">{log.reason}</span>
                      </div>
                    )}
                    {log.control_data && Object.keys(log.control_data).length > 0 && (
                      <div className="mt-2 bg-gray-50 rounded-md p-2">
                        <div className="text-xs text-gray-700">
                          {Object.entries(log.control_data).map(([key, value]) => (
                            <div key={key} className="mb-1">
                              <span className="text-gray-500 font-medium capitalize">{key.replace(/_/g, ' ')}:</span>{' '}
                              <span className="text-gray-900">
                                {key === 'pricing_updates' && Array.isArray(value) ? (
                                  <div className="ml-2 mt-1">
                                    {value.map((update: any, idx: number) => (
                                      <div key={idx} className="text-xs">
                                        • {update.service_type}: ${update.new_pricing} per {update.new_charge_type.replace('_', ' ')}
                                      </div>
                                    ))}
                                  </div>
                                ) : key === 'service_pricing' && Array.isArray(value) ? (
                                  <div className="ml-2 mt-1">
                                    {value.map((update: any, idx: number) => (
                                      <div key={idx} className="text-xs">
                                        • {update.service_type}: ${update.new_pricing} per {update.new_charge_type.replace('_', ' ')}
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  typeof value === 'object' ? JSON.stringify(value) : String(value)
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <div className="flex justify-end">
        <Button
          variant="ghost"
          size="sm"
          onClick={fetchLogs}
          disabled={loading}
        >
          <svg className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Logs
        </Button>
      </div>
    </div>
  );
}