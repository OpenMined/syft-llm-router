import { h } from 'preact';
import { JSX } from 'preact/compat';
import { useTheme } from './ThemeContext';

interface ButtonProps extends Omit<JSX.HTMLAttributes<HTMLButtonElement>, 'type'> {
  variant?: 'primary' | 'secondary' | 'success' | 'error' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: h.JSX.Element | string | (h.JSX.Element | string)[];
  disabled?: boolean;
  type?: 'submit' | 'reset' | 'button';
  color?: 'indigo' | 'teal'; // Optional override
}

const PRIMARY_CLASSES = {
  indigo: 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500',
  teal: 'bg-teal-500 text-white hover:bg-teal-600 focus:ring-teal-400',
};

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  loading = false,
  disabled,
  className = '',
  children,
  color,
  ...props 
}: ButtonProps) {
  let themeColor: 'indigo' | 'teal' = 'indigo';
  try {
    themeColor = color || useTheme().color;
  } catch {
    themeColor = color || 'indigo';
  }

  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: PRIMARY_CLASSES[themeColor],
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    success: 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500',
    error: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 focus:ring-gray-500 border border-gray-300'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
} 