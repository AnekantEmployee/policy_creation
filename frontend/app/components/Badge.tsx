import React from 'react';

type Variant = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
type Size = 'sm' | 'md' | 'lg';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
  size?: Size;
  dot?: boolean;
  icon?: React.ReactNode;
}

const variantStyles: Record<Variant, string> = {
  primary:   'bg-primary-100 text-primary-800',
  secondary: 'bg-secondary-100 text-secondary-800',
  success:   'bg-green-100 text-green-800',
  warning:   'bg-amber-100 text-amber-800',
  error:     'bg-red-100 text-red-800',
  info:      'bg-blue-100 text-blue-800',
};

const sizeStyles: Record<Size, string> = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-0.5 text-xs',
  lg: 'px-3 py-1 text-sm',
};

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'primary', size = 'md', dot = false, icon, className = '', children, ...props }, ref) => (
    <span
      ref={ref}
      className={`inline-flex items-center gap-1.5 rounded-full font-medium ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
      {...props}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {icon && <span className="shrink-0">{icon}</span>}
      {children}
    </span>
  )
);
Badge.displayName = 'Badge';
