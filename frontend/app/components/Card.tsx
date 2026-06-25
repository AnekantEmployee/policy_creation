import React from 'react';

/* ── Card ─────────────────────────────────────────── */
interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  interactive?: boolean;
}

const variantStyles = {
  default:  'bg-white border border-neutral-200 shadow-sm hover:shadow-md',
  elevated: 'bg-white shadow-lg',
  outlined: 'bg-white border-2 border-primary-200',
};

const paddingStyles = {
  none: '',
  sm:   'p-4',
  md:   'p-6',
  lg:   'p-8',
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ variant = 'default', padding = 'md', interactive = false, className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`rounded-xl transition-all duration-300 ${variantStyles[variant]} ${paddingStyles[padding]} ${interactive ? 'cursor-pointer hover:shadow-lg' : ''} ${className}`}
      {...props}
    />
  )
);
Card.displayName = 'Card';

/* ── CardHeader ───────────────────────────────────── */
interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, action, className = '', children, ...props }, ref) => (
    <div ref={ref} className={`mb-4 ${className}`} {...props}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {title && <h3 className="text-lg font-semibold text-neutral-900 truncate">{title}</h3>}
          {subtitle && <p className="text-sm text-neutral-500 mt-0.5">{subtitle}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </div>
  )
);
CardHeader.displayName = 'CardHeader';

/* ── CardBody ─────────────────────────────────────── */
export const CardBody = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div ref={ref} className={className} {...props} />
  )
);
CardBody.displayName = 'CardBody';

/* ── CardFooter ───────────────────────────────────── */
export const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = '', ...props }, ref) => (
    <div
      ref={ref}
      className={`mt-4 pt-4 border-t border-neutral-200 flex gap-2 ${className}`}
      {...props}
    />
  )
);
CardFooter.displayName = 'CardFooter';
