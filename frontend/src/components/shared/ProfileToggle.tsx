export type ProfileType = 'provider' | 'client' | 'gatekeeper';

interface ProfileToggleProps {
  profile: ProfileType;
  onChange: (profile: ProfileType) => void;
  trustedGatekeeping?: boolean;
}

export function ProfileToggle({ profile, onChange, trustedGatekeeping = false }: ProfileToggleProps) {
  // Utility for active/inactive button
  const getButtonClasses = (isActive: boolean, type: ProfileType) => {
    const accent = type === 'provider' ? 'indigo' : type === 'client' ? 'teal' : 'blue';
    if (isActive) {
      return [
        `bg-${accent}-600`,
        'text-white',
        'font-bold',
        'shadow',
        'transition-all',
        'duration-150',
        'px-6',
        'py-2',
        'rounded-full',
        'cursor-pointer',
        'focus:outline-none',
        `focus:ring-2 focus:ring-${accent}-400`,
        'z-10',
      ].join(' ');
    } else {
      return [
        'bg-white',
        `text-${accent}-700`,
        'font-semibold',
        'transition-all',
        'duration-150',
        'px-6',
        'py-2',
        'rounded-full',
        'cursor-pointer',
        'focus:outline-none',
        'focus:ring-2 focus:ring-gray-300',
        'hover:bg-gray-100',
        'z-0',
      ].join(' ');
    }
  };

  return (
    <div className="flex items-center rounded-full border border-gray-200 bg-gray-100 p-1 shadow-sm space-x-1">
      <button
        className={getButtonClasses(profile === 'provider', 'provider')}
        onClick={() => onChange('provider')}
        aria-pressed={profile === 'provider'}
        tabIndex={0}
        style={{ minWidth: 100 }}
      >
        Provider
      </button>
      <button
        className={getButtonClasses(profile === 'client', 'client')}
        onClick={() => onChange('client')}
        aria-pressed={profile === 'client'}
        tabIndex={0}
        style={{ minWidth: 100 }}
      >
        Client
      </button>
      {trustedGatekeeping && (
        <button
          className={getButtonClasses(profile === 'gatekeeper', 'gatekeeper')}
          onClick={() => onChange('gatekeeper')}
          aria-pressed={profile === 'gatekeeper'}
          tabIndex={0}
          style={{ minWidth: 100 }}
        >
          Gatekeeper
        </button>
      )}
    </div>
  );
} 