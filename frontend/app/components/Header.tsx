'use client';

import React from 'react';
import { Menu, Bell } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  compliance_officer: 'Compliance Officer',
  security_lead: 'Security Lead',
  executive: 'Executive',
  auditor: 'Auditor',
};

export const Header: React.FC<HeaderProps> = ({ title, subtitle, action }) => {
  const { setSidebarOpen } = useAppStore();
  const { user } = useAuthStore();

  // Derive the display initial from the logged-in user
  const initial = user?.full_name
    ? user.full_name.charAt(0).toUpperCase()
    : user?.username
      ? user.username.charAt(0).toUpperCase()
      : '?';

  const roleLabel = user?.role ? (ROLE_LABELS[user.role] ?? user.role) : '';

  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-neutral-200">
      <div className="flex items-center justify-between gap-4 px-6 py-4">
        {/* Left */}
        <div className="flex items-center gap-4 min-w-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-neutral-100 text-neutral-600 shrink-0"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          {title && (
            <div className="min-w-0">
              <h1 className="text-xl font-bold text-neutral-900 truncate">{title}</h1>
              {subtitle && <p className="text-sm text-neutral-500 mt-0.5 truncate">{subtitle}</p>}
            </div>
          )}
        </div>

        {/* Right */}
        <div className="flex items-center gap-2 shrink-0">
          {action}
          <button className="p-2 rounded-lg hover:bg-neutral-100 text-neutral-600" aria-label="Notifications">
            <Bell className="h-5 w-5" />
          </button>
          {/* User avatar with tooltip showing name + role */}
          <div
            className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-sm font-semibold cursor-default"
            title={user ? `${user.full_name || user.username} · ${roleLabel}` : ''}
            aria-label={user ? `Logged in as ${user.full_name || user.username}` : 'User avatar'}
          >
            {initial}
          </div>
        </div>
      </div>
    </header>
  );
};
