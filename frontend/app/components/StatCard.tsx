import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card, CardBody } from './Card';

type Color = 'primary' | 'secondary' | 'success' | 'warning' | 'error';

interface StatCardProps {
  icon?: LucideIcon;
  label: string;
  value: string | number;
  change?: { value: number; type: 'increase' | 'decrease' | 'neutral' };
  color?: Color;
  onClick?: () => void;
}

const iconBg: Record<Color, string> = {
  primary:   'bg-primary-100 text-primary-600',
  secondary: 'bg-secondary-100 text-secondary-600',
  success:   'bg-green-100 text-green-600',
  warning:   'bg-amber-100 text-amber-600',
  error:     'bg-red-100 text-red-600',
};

const changeColor = {
  increase: 'text-green-600',
  decrease: 'text-red-500',
  neutral:  'text-neutral-500',
};

const changeArrow = {
  increase: '↑',
  decrease: '↓',
  neutral:  '→',
};

export const StatCard: React.FC<StatCardProps> = ({
  icon: Icon,
  label,
  value,
  change,
  color = 'primary',
  onClick,
}) => (
  <Card interactive={!!onClick} onClick={onClick} className="overflow-hidden">
    <CardBody className="p-6">
      {Icon && (
        <div className={`inline-flex p-3 rounded-lg mb-4 ${iconBg[color]}`}>
          <Icon className="h-5 w-5" />
        </div>
      )}
      <p className="text-sm text-neutral-500 mb-1">{label}</p>
      <div className="flex items-end justify-between gap-2">
        <span className="text-2xl font-bold text-neutral-900">{value}</span>
        {change && (
          <span className={`text-xs font-semibold ${changeColor[change.type]}`}>
            {changeArrow[change.type]} {change.value}%
          </span>
        )}
      </div>
    </CardBody>
  </Card>
);
