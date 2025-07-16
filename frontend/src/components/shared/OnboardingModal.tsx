interface OnboardingModalProps {
  onSelect: (profile: 'provider' | 'client') => void;
}

export function OnboardingModal({ onSelect }: OnboardingModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30">
      <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-xl w-full text-center">
        <h2 className="text-3xl font-extrabold text-gray-900 mb-2 flex items-center justify-center">
          <span className="mr-2">🔒</span> Syft Routers: Your Data, Your Flow
        </h2>
        <div className="text-lg font-bold text-indigo-700 mb-4">Private. Secure. Effortless.</div>
        <p className="text-gray-600 mb-8 text-base">
          Spin up your own private router and share data or models securely—in just a few clicks.
        </p>
        <div className="flex flex-col gap-4">
          <button
            className="w-full py-2 rounded-lg bg-indigo-600 text-white font-semibold text-lg flex items-center justify-center hover:bg-indigo-700 shadow"
            onClick={() => onSelect('provider')}
          >
            <span className="mr-2">🛠</span> Provider Mode
          </button>
          <div className="text-xs text-gray-500 mb-2">Manage & publish routers</div>
          <button
            className="w-full py-2 rounded-lg bg-teal-500 text-white font-semibold text-lg flex items-center justify-center hover:bg-teal-600 shadow"
            onClick={() => onSelect('client')}
          >
            <span className="mr-2">🌐</span> Client Mode
          </button>
          <div className="text-xs text-gray-500">Browse & use published routers</div>
        </div>
      </div>
    </div>
  );
} 