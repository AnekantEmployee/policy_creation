'use client';

import React from 'react';
import { useAppStore } from '@/store/appStore';

export const MainContent: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  return (
    <div
      className={`min-h-screen flex flex-col transition-all duration-300 ease-in-out ${
        sidebarOpen ? 'lg:pl-60' : 'lg:pl-14'
      }`}
    >
      {children}
    </div>
  );
};
