'use client';

import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  inputSize?: 'sm' | 'md' | 'lg';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      helperText,
      icon,
      iconPosition = 'left',
      inputSize = 'md',
      className = '',
      ...props
    },
    ref
  ) => {
    const sizeStyle = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2.5 text-sm',
      lg: 'px-5 py-3 text-base',
    }[inputSize];

    const iconPad = icon
      ? iconPosition === 'left'
        ? 'pl-10'
        : 'pr-10'
      : '';

    const borderStyle = error
      ? 'border-error focus:border-error focus:bg-red-50'
      : 'border-neutral-200 focus:border-primary-500 focus:bg-primary-50';

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-neutral-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && iconPosition === 'left' && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            className={`w-full rounded-lg border-2 bg-white text-neutral-900 placeholder:text-neutral-400 outline-none transition-all duration-200 ${sizeStyle} ${borderStyle} ${iconPad} ${className}`}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none">
              {icon}
            </div>
          )}
        </div>
        {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
        {helperText && !error && (
          <p className="text-neutral-500 text-xs mt-1">{helperText}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
