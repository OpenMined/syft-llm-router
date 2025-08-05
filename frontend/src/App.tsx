import { useState, useEffect } from 'preact/hooks';
import { RouterList } from './components/router/RouterList';
import { RouterDetailPage } from './components/router/RouterDetailPage';
import { ChatPage } from './components/chat/ChatPage';
import { UsagePage } from './components/usage/UsagePage';
import { Header } from './components/shared/Header';
import { ProfileToggle, ProfileType } from './components/shared/ProfileToggle';
import { OnboardingModal } from './components/shared/OnboardingModal';
import { PasswordUpdateModal } from './components/shared/PasswordUpdateModal';
import { AccountingSetupModal } from './components/shared/AccountingSetupModal';
import { ThemeContext } from './components/shared/ThemeContext';
import { accountingService, type UserAccount } from './services/accountingService';

const PROFILE_KEY = 'syftbox_profile';

// Simple route state
export function App() {
  const [route, setRoute] = useState<{ page: 'list' } | { page: 'detail'; routerName: string; published: boolean; author: string } | { page: 'chat' } | { page: 'usage' }>({ page: 'list' });
  const [activeTab, setActiveTab] = useState<'routers' | 'chat' | 'usage'>('routers');
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showPasswordUpdate, setShowPasswordUpdate] = useState(false);
  const [showAccountingSetup, setShowAccountingSetup] = useState(false);
  const [currentEmail, setCurrentEmail] = useState('');
  const [accountingUrl, setAccountingUrl] = useState('');
  const [accountingSetupReason, setAccountingSetupReason] = useState<'no_credentials' | 'auth_failed'>('no_credentials');

  // Load profile from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(PROFILE_KEY) as ProfileType | null;
    if (stored === 'provider' || stored === 'client') {
      setProfile(stored);
      // After profile is loaded, validate account
      validateAccount();
    } else {
      setShowOnboarding(true);
    }
  }, []);

  // Validate account connection
  const validateAccount = async () => {
    const accountResponse = await accountingService.getAccountInfo();
    
    if (accountResponse.success && accountResponse.data) {
      // Account is valid - hide all modals and proceed to router detail page
      setCurrentEmail(accountResponse.data.email);
      setShowOnboarding(false);
      setShowPasswordUpdate(false);
      setShowAccountingSetup(false);
    } else if (accountResponse.statusCode === 401) {
      // Invalid credentials (incorrect password), get email from username API and show password update modal
      const usernameResponse = await accountingService.getUsername();
      if (usernameResponse.success && usernameResponse.data) {
        setCurrentEmail(usernameResponse.data.username);
      }
      
      const urlResponse = await accountingService.getAccountingUrl();
      if (urlResponse.success && urlResponse.data) {
        setAccountingUrl(urlResponse.data);
      }
      setShowOnboarding(false); // Hide onboarding to show password update modal
      setShowPasswordUpdate(true);
      setShowAccountingSetup(false);
    } else if (accountResponse.statusCode === 404) {
      // No credentials found in database, show accounting setup modal
      const usernameResponse = await accountingService.getUsername();
      if (usernameResponse.success && usernameResponse.data) {
        setCurrentEmail(usernameResponse.data.username);
      }
      
      const urlResponse = await accountingService.getAccountingUrl();
      if (urlResponse.success && urlResponse.data) {
        setAccountingUrl(urlResponse.data);
      }
      setAccountingSetupReason('no_credentials');
      setShowOnboarding(false); // Hide onboarding to show accounting setup modal
      setShowAccountingSetup(true);
      setShowPasswordUpdate(false);
    }
  };

  // Persist profile to localStorage
  useEffect(() => {
    if (profile) {
      localStorage.setItem(PROFILE_KEY, profile);
      // Don't hide onboarding here - let validateAccount handle it
    }
  }, [profile]);

  // Handler for clicking a router in the list
  const handleRouterClick = (routerName: string, published: boolean, author: string) => {
    setRoute({ page: 'detail', routerName, published, author });
  };

  // Handler for going back to the list
  const handleBackToList = () => {
    setRoute({ page: 'list' });
    setActiveTab('routers');
  };

  // Handler for tab changes
  const handleTabChange = (tab: 'routers' | 'chat' | 'usage') => {
    setActiveTab(tab);
    if (tab === 'routers') {
      setRoute({ page: 'list' });
    } else if (tab === 'chat') {
      setRoute({ page: 'chat' });
    } else if (tab === 'usage') {
      setRoute({ page: 'usage' });
    }
  };

  // Handler for onboarding modal - now validates account after profile selection
  const handleOnboardingSelect = async (selected: ProfileType) => {
    setProfile(selected);
    // After profile is set, validate account
    await validateAccount();
  };

  // Handler for password update modal
  const handlePasswordUpdateSuccess = (account: UserAccount) => {
    setShowPasswordUpdate(false);
    setShowOnboarding(false);
    setShowAccountingSetup(false);
    setCurrentEmail(account.email);
  };

  const handlePasswordUpdateClose = () => {
    setShowPasswordUpdate(false);
    // If user cancels password update, show onboarding
    setShowOnboarding(true);
  };

  // Handler for accounting setup modal
  const handleAccountingSetupSuccess = (account: UserAccount) => {
    setShowAccountingSetup(false);
    setShowOnboarding(false);
    setShowPasswordUpdate(false);
    setCurrentEmail(account.email);
  };

  const handleAccountingSetupClose = () => {
    setShowAccountingSetup(false);
    // If user cancels accounting setup, show onboarding
    setShowOnboarding(true);
  };

  // Handler for profile toggle
  const handleProfileToggle = (newProfile: ProfileType) => {
    setProfile(newProfile);
  };

  return (
    <ThemeContext.Provider value={profile ? { profile, color: profile === 'provider' ? 'indigo' : 'teal' } : { profile: 'provider', color: 'indigo' }}>
      <div className="min-h-screen relative bg-white">
        {/* Only render dashboard if profile is chosen and no modals are showing */}
        {profile && !showOnboarding && !showPasswordUpdate && !showAccountingSetup && (
          <div>
            <Header 
              profileToggle={<ProfileToggle profile={profile} onChange={handleProfileToggle} />}
              onTabChange={handleTabChange}
              activeTab={activeTab}
            />
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {route.page === 'list' ? (
                <RouterList onRouterClick={handleRouterClick} profile={profile} />
              ) : route.page === 'detail' ? (
                <RouterDetailPage
                  routerName={route.routerName}
                  published={route.published}
                  author={route.author}
                  onBack={handleBackToList}
                  profile={profile}
                />
              ) : route.page === 'chat' ? (
                <ChatPage onBack={handleBackToList} />
              ) : (
                <UsagePage />
              )}
            </div>
          </div>
        )}
        {showOnboarding && <OnboardingModal onSelect={handleOnboardingSelect} />}
        {showPasswordUpdate && (
          <PasswordUpdateModal
            isOpen={showPasswordUpdate}
            onClose={handlePasswordUpdateClose}
            onSuccess={handlePasswordUpdateSuccess}
            email={currentEmail}
            accountingUrl={accountingUrl}
          />
        )}
        {showAccountingSetup && (
          <AccountingSetupModal
            isOpen={showAccountingSetup}
            onClose={handleAccountingSetupClose}
            onSuccess={handleAccountingSetupSuccess}
            email={currentEmail}
            accountingUrl={accountingUrl}
            reason={accountingSetupReason}
          />
        )}
      </div>
    </ThemeContext.Provider>
  );
} 