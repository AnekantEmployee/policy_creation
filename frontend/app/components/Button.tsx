'use client';

import React from 'react';

type Variant = 'primary' | 'secondary' | 'accent' | 'ghost' | 'outline';
type Size = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variantStyles: Record<Variant, string> = {
  primary:
    'bg-primary-600 text-white shadow-sm hover:bg-primary-700 active:bg-primary-800',
  secondary:
    'bg-secondary-600 text-white shadow-sm hover:bg-secondary-700 active:bg-secondary-800',
  accent:
    'bg-accent-600 text-white shadow-sm hover:bg-accent-700 active:bg-accent-800',
  ghost:
    'text-primary-600 bg-transparent hover:bg-primary-50 active:bg-primary-100',
  outline:
    'border-2 border-neutral-300 text-neutral-700 bg-transparent hover:border-primary-600 hover:text-primary-600 active:bg-primary-50',
};

const sizeStyles: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      className = '',
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const base =
      'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={`${base} ${variantStyles[variant]} ${sizeStyles[size]} ${fullWidth ? 'w-full' : ''} ${className}`}
        {...props}
      >
        {icon && iconPosition === 'left' && !isLoading && icon}
        {isLoading && (
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" />
        )}
        {children}
        {icon && iconPosition === 'right' && !isLoading && icon}
      </button>
    );
  }
);

Button.displayName = 'Button';
