import { createContext } from 'preact';
import { useContext } from 'preact/hooks';
import { ProfileType } from './ProfileToggle';

export type Theme = {
  profile: ProfileType;
  color: 'indigo' | 'teal';
};

export const ThemeContext = createContext<Theme | undefined>(undefined);

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within a ThemeContext.Provider');
  return ctx;
}

// Utility for mapping theme color to Tailwind classes
export function themeClass(color: 'indigo' | 'teal') {
  return {
    bg50: color === 'indigo' ? 'bg-indigo-50' : 'bg-teal-50',
    bg100: color === 'indigo' ? 'bg-indigo-100' : 'bg-teal-100',
    bg600: color === 'indigo' ? 'bg-indigo-600' : 'bg-teal-500',
    bg700: color === 'indigo' ? 'bg-indigo-700' : 'bg-teal-600',
    border600: color === 'indigo' ? 'border-indigo-600' : 'border-teal-500',
    border400: color === 'indigo' ? 'border-indigo-400' : 'border-teal-400',
    text600: color === 'indigo' ? 'text-indigo-600' : 'text-teal-500',
    text700: color === 'indigo' ? 'text-indigo-700' : 'text-teal-600',
    ring500: color === 'indigo' ? 'ring-indigo-500' : 'ring-teal-400',
    focusRing: color === 'indigo' ? 'focus:ring-indigo-500' : 'focus:ring-teal-400',
  };
} 