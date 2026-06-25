'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { MainContent } from './MainContent';
import { useAuth } from '@/hooks/useAuth';

// Routes where sidebar should NOT appear
const AUTH_ROUTES = ['/auth'];

export const ConditionalLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const pathname = usePathname();
  // Wire up token refresh and auth initialization for the whole app
  useAuth();

  const isAuthRoute = AUTH_ROUTES.some(r => pathname.startsWith(r));

  if (isAuthRoute) {
    return <>{children}</>;
  }

  return (
    <>
      <Sidebar />
      <MainContent>{children}</MainContent>
    </>
  );
};
