'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { FileText, Settings, Zap, ChevronLeft, Menu, X, LogOut, Shield } from 'lucide-react';
import { useAppStore } from '@/store/appStore';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

// Roles that can create/generate new compliance content
const WRITE_ROLES = ['admin', 'compliance_officer'];

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  compliance_officer: 'Compliance Officer',
  security_lead: 'Security Lead',
  executive: 'Executive',
  auditor: 'Auditor',
};

// Base nav — visible to all authenticated roles
const baseNavItems = [
  { name: 'History',  href: '/history',  icon: FileText, description: 'Past generations' },
  { name: 'Settings', href: '/settings', icon: Settings, description: 'System configuration' },
];

// Restricted nav — only for roles that can generate content
const writeNavItem = { name: 'New Scan', href: '/wizard', icon: Zap, description: 'Generate compliance docs' };

const adminNavItem = { name: 'Admin', href: '/admin', icon: Shield, description: 'User management' };

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const router = useRouter();
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  const { user, logout, isAuthenticated, initializeFromStorage } = useAuthStore();

  // Hydrate auth state once on mount
  useEffect(() => {
    initializeFromStorage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Close on mobile when route changes
  useEffect(() => {
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  }, [pathname, setSidebarOpen]);

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
      router.push('/auth');
    } catch {
      toast.error('Logout failed');
    }
  };

  const canWrite = user?.role ? WRITE_ROLES.includes(user.role) : false;
  const roleLabel = user?.role ? (ROLE_LABELS[user.role] ?? user.role) : '';

  // Build the ordered nav list: New Scan first (write-only), then base items
  const visibleNavItems = [
    ...(canWrite ? [writeNavItem] : []),
    ...baseNavItems,
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 lg:hidden z-40 transition-opacity"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar panel */}
      <aside
        className={`
          fixed left-0 top-0 z-50 h-screen
          bg-gradient-to-b from-neutral-900 via-neutral-900 to-primary-900
          border-r border-neutral-800
          flex flex-col
          transition-all duration-300 ease-in-out
          ${sidebarOpen ? 'w-60' : 'w-14'}
          overflow-hidden
        `}
        aria-label="Main navigation"
      >
        {/* Logo / header */}
        <div className={`flex items-center border-b border-neutral-800 h-16 shrink-0 px-3 justify-center`}>
          {sidebarOpen ? (
            <div className="flex items-center gap-3 min-w-0">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center shadow-lg shrink-0">
                <Zap className="h-4 w-4 text-white" />
              </div>
              <div className="min-w-0">
                <span className="font-bold text-white text-sm leading-tight block truncate">GRC AI</span>
                <p className="text-neutral-400 text-xs truncate">Policy Creator</p>
              </div>
            </div>
          ) : (
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center shadow-lg">
              <Zap className="h-4 w-4 text-white" />
            </div>
          )}
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-3 space-y-0.5 overflow-y-auto overflow-x-hidden px-2">
          {visibleNavItems.map(({ name, href, icon: Icon, description }) => {
            const active = pathname === href || (href !== '/' && pathname.startsWith(href));
            return (
              <Link key={href} href={href}>
                <div
                  title={!sidebarOpen ? name : undefined}
                  className={`
                    flex items-center gap-3 py-2.5 rounded-xl text-sm font-medium
                    transition-all duration-200 cursor-pointer
                    ${sidebarOpen ? 'px-3' : 'px-0 justify-center'}
                    ${active
                      ? 'bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-md shadow-primary-900/40'
                      : 'text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/70'}
                  `}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {sidebarOpen && (
                    <div className="min-w-0 flex-1">
                      <span className="block truncate">{name}</span>
                      {!active && <span className="block text-xs text-neutral-500 font-normal truncate">{description}</span>}
                    </div>
                  )}
                </div>
              </Link>
            );
          })}

          {/* Admin link - only show if user is admin */}
          {user?.role === 'admin' && (
            <>
              <div className="py-2 px-2">
                <div className="h-px bg-neutral-700" />
              </div>
              <Link href={adminNavItem.href}>
                <div
                  title={!sidebarOpen ? adminNavItem.name : undefined}
                  className={`
                    flex items-center gap-3 py-2.5 rounded-xl text-sm font-medium
                    transition-all duration-200 cursor-pointer
                    ${sidebarOpen ? 'px-3' : 'px-0 justify-center'}
                    ${pathname === adminNavItem.href || pathname.startsWith(adminNavItem.href)
                      ? 'bg-gradient-to-r from-red-600 to-red-500 text-white shadow-md shadow-red-900/40'
                      : 'text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/70'}
                  `}
                >
                  <adminNavItem.icon className="h-4 w-4 shrink-0" />
                  {sidebarOpen && (
                    <div className="min-w-0 flex-1">
                      <span className="block truncate">{adminNavItem.name}</span>
                      {pathname !== adminNavItem.href && <span className="block text-xs text-neutral-500 font-normal truncate">{adminNavItem.description}</span>}
                    </div>
                  )}
                </div>
              </Link>
            </>
          )}
        </nav>

        {/* Bottom controls */}
        <div className="border-t border-neutral-800 p-2 mt-auto space-y-2">
          {/* User profile section - show if authenticated */}
          {isAuthenticated && user && (
            <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${sidebarOpen ? '' : 'justify-center'}`}>
              {sidebarOpen ? (
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
                    {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-neutral-200 text-xs font-medium truncate">{user.full_name || user.username}</p>
                    <p className="text-neutral-500 text-xs truncate">{roleLabel}</p>
                  </div>
                </div>
              ) : (
                <div
                  className="h-8 w-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-xs font-bold"
                  title={`${user.full_name || user.username} · ${roleLabel}`}
                >
                  {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.username.charAt(0).toUpperCase()}
                </div>
              )}
            </div>
          )}

          {/* Logout button - show if authenticated */}
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/70 transition-all"
              title="Logout"
            >
              <LogOut className="h-4 w-4" />
              {sidebarOpen && <span>Logout</span>}
            </button>
          )}

          {/* Collapse/Expand button */}
          {sidebarOpen ? (
            <button
              onClick={() => setSidebarOpen(false)}
              className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-sm text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/70 transition-all"
              aria-label="Collapse sidebar"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Collapse</span>
            </button>
          ) : (
            <button
              onClick={() => setSidebarOpen(true)}
              className="w-full flex items-center justify-center p-2.5 rounded-lg text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/70 transition-all"
              aria-label="Expand sidebar"
              title="Expand sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
          )}
        </div>
      </aside>
    </>
  );
};

// Hamburger button for mobile (rendered in page headers)
export const SidebarToggle: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useAppStore();
  return (
    <button
      onClick={() => setSidebarOpen(!sidebarOpen)}
      className="p-2.5 rounded-lg text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 transition-colors lg:hidden"
      aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
    >
      {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
    </button>
  );
};
