import { useState, useEffect } from 'preact/hooks';
import { accountingService, type CreateAccountRequest, type UpdateCredentialsRequest, type UserAccount } from '../../services/accountingService';

interface AccountModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (account: UserAccount) => void;
  initialEmail?: string;
}

type ModalStep = 'create' | 'exists' | 'password' | 'success';

export function AccountModal({ isOpen, onClose, onSuccess, initialEmail }: AccountModalProps) {
  const [step, setStep] = useState<ModalStep>('create');
  const [email, setEmail] = useState(initialEmail || '');
  const [password, setPassword] = useState('');
  const [organization, setOrganization] = useState('');
  const [accountingUrl, setAccountingUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [createdAccount, setCreatedAccount] = useState<UserAccount | null>(null);

  useEffect(() => {
    if (isOpen) {
      setEmail(initialEmail || '');
      setPassword('');
      setOrganization('');
      setError('');
      setCreatedAccount(null);
      
      // If we have an initialEmail, start with the "exists" step
      // This handles the 409 case where account creation failed because account exists
      if (initialEmail) {
        setStep('exists');
      } else {
        setStep('create');
      }
      
      loadAccountingUrl();
    }
  }, [isOpen, initialEmail]);

  const loadAccountingUrl = async () => {
    const response = await accountingService.getAccountingUrl();
    if (response.success && response.data) {
      setAccountingUrl(response.data);
    }
  };

  const handleCreateAccount = async () => {
    if (!email.trim()) {
      setError('Email is required');
      return;
    }

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
      setError(response.error || 'Failed to update credentials');
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4">
        {step === 'create' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Create Account
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail((e.target as HTMLInputElement).value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter your email"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Organization (Optional)
                </label>
                <input
                  type="text"
                  value={organization}
                  onChange={(e) => setOrganization((e.target as HTMLInputElement).value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter organization name"
                />
              </div>
              {error && (
                <div className="text-red-600 text-sm">{error}</div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={onClose}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateAccount}
                  disabled={isLoading}
                  className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isLoading ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'exists' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Account Already Exists
            </h2>
            <div className="space-y-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-blue-800 mb-2">Great! We found an existing account with your email. Please provide your password to connect.</p>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-blue-600">Accounting URL:</span>
                    <p 
                      className="text-sm text-blue-900 truncate" 
                      title={accountingUrl}
                    >
                      {accountingUrl}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-blue-600">Email:</span>
                    <p className="text-sm text-blue-900">{email}</p>
                  </div>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword((e.target as HTMLInputElement).value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Enter your password"
                />
              </div>
              {error && (
                <div className="text-red-600 text-sm">{error}</div>
              )}
              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setStep('create')}
                  className="flex-1 py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleUpdatePassword}
                  disabled={isLoading}
                  className="flex-1 py-2 px-4 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {isLoading ? 'Updating...' : 'Update Credentials'}
                </button>
              </div>
            </div>
          </div>
        )}

        {step === 'success' && (
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Account Created Successfully!
            </h2>
            <div className="space-y-4">
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-green-800 mb-2">Your account has been created successfully.</p>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs font-medium text-green-600">Email:</span>
                    <p className="text-sm text-green-900">{email}</p>
                  </div>
                  <div>
                    <span className="text-xs font-medium text-green-600">Password:</span>
                    <p className="text-sm text-green-900 font-mono">{createdAccount?.password || password || 'Generated password'}</p>
                  </div>
                </div>
              </div>
              <div className="pt-4">
                <button
                  onClick={handleSuccess}
                  className="w-full py-2 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700"
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