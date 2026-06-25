'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LandingPage } from './landing';
import { useAuthStore } from '@/store/authStore';

export default function Home(_props: PageProps<'/'>) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  // Initialize auth from storage on mount
  useEffect(() => {
    useAuthStore.getState().initializeFromStorage();
  }, []);

  // Redirect to auth if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, router]);

  // Show loading or landing page only if authenticated
  if (!isAuthenticated) {
    return <div className="min-h-screen bg-neutral-900 flex items-center justify-center" />;
  }

  return <LandingPage />;
}
