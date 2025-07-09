import { useState, useEffect } from 'preact/hooks';
import { RouterList } from './components/router/RouterList';
import { RouterDetailPage } from './components/router/RouterDetailPage';
import { Header } from './components/shared/Header';
import { ProfileToggle, ProfileType } from './components/shared/ProfileToggle';
import { OnboardingModal } from './components/shared/OnboardingModal';
import { ThemeContext } from './components/shared/ThemeContext';

const PROFILE_KEY = 'syftbox_profile';

// Simple route state
export function App() {
  const [route, setRoute] = useState<{ page: 'list' } | { page: 'detail'; routerName: string; published: boolean }>({ page: 'list' });
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [showOnboarding, setShowOnboarding] = useState(false);

  // Load profile from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(PROFILE_KEY) as ProfileType | null;
    if (stored === 'provider' || stored === 'client') {
      setProfile(stored);
    } else {
      setShowOnboarding(true);
    }
  }, []);

  // Persist profile to localStorage
  useEffect(() => {
    if (profile) {
      localStorage.setItem(PROFILE_KEY, profile);
      setShowOnboarding(false);
    }
  }, [profile]);

  // Handler for clicking a router in the list
  const handleRouterClick = (routerName: string, published: boolean) => {
    setRoute({ page: 'detail', routerName, published });
  };

  // Handler for going back to the list
  const handleBackToList = () => {
    setRoute({ page: 'list' });
  };

  // Handler for onboarding modal
  const handleOnboardingSelect = (selected: ProfileType) => {
    setProfile(selected);
  };

  // Handler for profile toggle
  const handleProfileToggle = (newProfile: ProfileType) => {
    setProfile(newProfile);
  };

  return (
    <ThemeContext.Provider value={profile ? { profile, color: profile === 'provider' ? 'indigo' : 'teal' } : { profile: 'provider', color: 'indigo' }}>
      <div className="min-h-screen relative bg-white">
        {/* Only render dashboard if profile is chosen */}
        {profile && !showOnboarding && (
          <div>
            <Header profile={profile} profileToggle={<ProfileToggle profile={profile} onChange={handleProfileToggle} />} />
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {route.page === 'list' ? (
                <RouterList onRouterClick={handleRouterClick} profile={profile} />
              ) : (
                <RouterDetailPage
                  routerName={route.routerName}
                  published={route.published}
                  onBack={handleBackToList}
                  profile={profile}
                />
              )}
            </div>
          </div>
        )}
        {showOnboarding && <OnboardingModal onSelect={handleOnboardingSelect} />}
      </div>
    </ThemeContext.Provider>
  );
} 