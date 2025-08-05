import { useState, useEffect } from 'preact/hooks';
import { accountingService, type CreateAccountRequest, type UpdateCredentialsRequest, type UserAccount } from '../../services/accountingService';

interface AccountingSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  email: string;
  accountingUrl: string;
  reason: 'no_credentials' | 'auth_failed';
}

type ModalStep = 'create' | 'exists' | 'password' | 'success';

export function AccountingSetupModal({ 
  isOpen, 
  onClose, 
  onSuccess, 
  email, 
  accountingUrl, 
  reason 
}: AccountingSetupModalProps) {
  const [step, setStep] = useState<ModalStep>('create');
  const [password, setPassword] = useState('');
  const [organization, setOrganization] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdAccount, setCreatedAccount] = useState<UserAccount | null>(null);

  useEffect(() => {
    if (isOpen) {
      setPassword('');
      setOrganization('');
      setError('');
      setCreatedAccount(null);
      setStep('create');
    }
  }, [isOpen]);

  // Customize modal content based on reason
  const getModalTitle = () => {
    if (reason === 'auth_failed') {
      return 'Reconnect to Accounting Service';
    }
    return 'Register with Accounting Service';
  };

  const getModalDescription = () => {
    if (reason === 'auth_failed') {
      return 'Your accounting service connection has failed. Please provide your credentials to reconnect.';
    }
    return 'Connect your account to the accounting service to enable secure transactions.';
  };

  const handleCreateAccount = async () => {
    setIsLoading(true);
    setError('');

    const request: CreateAccountRequest = {
      email: email.trim(),
      organization: organization.trim() || undefined,
    };

    const response = await accountingService.createAccount(request);

    setIsLoading(false);

    if (response.success && response.data) {
      // Account created successfully
      setCreatedAccount(response.data);
      setPassword(response.data.password);
      setStep('success');
    } else if (response.statusCode === 409) {
      // Account already exists, move to password step
      setStep('exists');
    } else {
      setError(response.error || 'Failed to create account');
    }
  };

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
      organization: organization.trim() || undefined,
    };

    const response = await accountingService.updateCredentials(request);

    setIsLoading(false);

    if (response.success && response.data) {
      setCreatedAccount(response.data);
      setPassword(response.data.password);
      setStep('success');
    } else {
      // Show user-friendly error message
      if (response.statusCode === 401) {
        setError('Invalid credentials. Please check your password and try again.');
      } else {
        setError(response.error || 'Failed to update credentials. Please try again.');
      }
    }
  };

  const handleSuccess = () => {
    if (createdAccount) {
      onSuccess(createdAccount);
    } else {
      // Fallback if createdAccount is not set
      const account: UserAccount = {
        email: email.trim(),
        password: password.trim(),
        organization: organization.trim() || undefined,
        balance: 0,
      };
      onSuccess(account);
    }
    onClose();
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
        {step === 'create' && (
          <div>
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔐</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                {getModalTitle()}
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                {getModalDescription()}
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-100">
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-indigo-700">Email</span>
                    <p className="text-sm text-indigo-900 font-mono">{email}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-indigo-700">Service URL</span>
                    <p 
                      className="text-sm text-indigo-900 font-mono truncate" 
                      title={accountingUrl}
                    >
                      {accountingUrl}
                    </p>
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={organization}
                  onChange={(e) => setOrganization((e.target as HTMLInputElement).value)}
                  className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all duration-200"
                  placeholder="Enter organization name"
                />
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
                  onClick={handleCreateAccount}
                  disabled={isLoading}
                  className="flex-1 py-2.5 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all duration-200 font-medium flex items-center justify-center"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating...
                    </>
                  ) : (
                    'Continue'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'exists' && (
          <div>
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">👤</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                Account Already Exists
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                We found an existing account with your email. Please provide your password to connect.
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-blue-700">Email</span>
                    <p className="text-sm text-blue-900 font-mono">{email}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-blue-700">Service URL</span>
                    <p 
                      className="text-sm text-blue-900 font-mono truncate" 
                      title={accountingUrl}
                    >
                      {accountingUrl}
                    </p>
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
                  onClick={() => setStep('create')}
                  className="flex-1 py-2.5 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-all duration-200 font-medium"
                >
                  Back
                </button>
                <button
                  onClick={handleUpdatePassword}
                  disabled={isLoading}
                  className="flex-1 py-2.5 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-all duration-200 font-medium"
                >
                  {isLoading ? 'Updating...' : 'Connect Account'}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div>
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">✅</span>
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                Account Connected Successfully!
              </h2>
              <p className="text-sm text-gray-600 mt-2">
                Your account has been connected to the accounting service.
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-green-700">Email</span>
                    <p className="text-sm text-green-900 font-mono">{email}</p>
                  </div>
                  {createdAccount?.password && (
                    <div>
                      <span className="text-xs font-medium text-green-700">Password</span>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-sm text-green-900 font-mono break-all flex-1">
                          {createdAccount.password}
                        </p>
                        <button
                          onClick={async () => {
                            const success = await copyToClipboard(createdAccount.password);
                            if (success) {
                              setCopySuccess(true);
                              setTimeout(() => setCopySuccess(false), 2000); // Reset after 2 seconds
                            } else {
                              console.error('Failed to copy password');
                            }
                          }}
                          className={`px-2 py-1 text-xs rounded transition-all duration-200 flex-shrink-0 font-medium ${
                            copySuccess 
                              ? 'bg-green-200 text-green-800' 
                              : 'bg-green-100 text-green-700 hover:bg-green-200'
                          }`}
                          title="Copy password"
                        >
                          {copySuccess ? '✅ Copied!' : '📋 Copy'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="pt-2">
                <button
                  onClick={handleSuccess}
                  className="w-full py-2.5 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all duration-200 font-medium"
                >
                  Continue
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
} 