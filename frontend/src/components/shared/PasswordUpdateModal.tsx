import { useState } from 'preact/hooks';
import { accountingService, type UpdateCredentialsRequest, type UserAccount } from '../../services/accountingService';

interface PasswordUpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  email: string;
  accountingUrl: string;
}

export function PasswordUpdateModal({ isOpen, onClose, onSuccess, email, accountingUrl }: PasswordUpdateModalProps) {
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleUpdatePassword = async () => {
    if (!password.trim()) {
      setError('Password is required');
      return;
    }

    setIsLoading(true);
    setError('');

    const request: UpdateCredentialsRequest = {
      email: email.trim(),
      password: password.trim(),
    };

    const response = await accountingService.updateCredentials(request);

    setIsLoading(false);

    if (response.success && response.data) {
      onSuccess(response.data);
      onClose();
    } else {
      // Show user-friendly error message
      if (response.statusCode === 401) {
        setError('Invalid credentials. Please check your password and try again.');
      } else {
        setError(response.error || 'Failed to update password. Please try again.');
      }
    }
  };

  const handleForgotPassword = () => {
    // Open email client with support email
    const subject = encodeURIComponent('Password Reset Request - SyftBox Accounting Service');
    const body = encodeURIComponent(`Hello Support Team,\n\nI need help resetting my password for the SyftBox accounting service.\n\nEmail: ${email}\nAccounting URL: ${accountingUrl}\n\nThank you.`);
    window.open(`mailto:support@openmined.org?subject=${subject}&body=${body}`);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4 border border-gray-100">
        <div className="text-center mb-6">
          <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🔑</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-900">
            Update Password
          </h2>
          <p className="text-sm text-gray-600 mt-2">
            Authorization failed with the accounting service. Please provide the correct password to continue.
          </p>
        </div>
        
        <div className="space-y-4">
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-100">
            <div className="space-y-2">
              <div>
                <span className="text-xs font-medium text-yellow-700">Email</span>
                <p className="text-sm text-yellow-900 font-mono">{email}</p>
              </div>
              <div>
                <span className="text-xs font-medium text-yellow-700">Service URL</span>
                <p className="text-sm text-yellow-900 font-mono">{accountingUrl}</p>
              </div>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword((e.target as HTMLInputElement).value)}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200"
              placeholder="Enter your password"
            />
            <div className="mt-2">
              <button
                onClick={handleForgotPassword}
                className="text-xs text-indigo-600 hover:text-indigo-800 underline transition-colors"
                title="Click to email support@openmined.org for password reset"
              >
                Forgot Password?
              </button>
            </div>
          </div>
          
          {error && (
            <div className="flex items-start space-x-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <span className="text-red-500 mt-0.5">⚠️</span>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          
          <div className="flex gap-3 pt-2">
            <button
              onClick={onClose}
              className="flex-1 py-2.5 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-all duration-200 font-medium"
            >
              Cancel
            </button>
            <button
              onClick={handleUpdatePassword}
              disabled={isLoading}
              className="flex-1 py-2.5 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all duration-200 font-medium"
            >
              {isLoading ? 'Updating...' : 'Update Password'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 