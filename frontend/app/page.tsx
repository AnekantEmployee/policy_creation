'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { LandingPage } from './landing';
import { useAuthStore } from '@/store/authStore';

export default function Home(_props: PageProps<'/'>) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const [hydrated, setHydrated] = useState(false);

  // Initialize auth from storage on mount, then mark hydrated
  useEffect(() => {
    useAuthStore.getState().initializeFromStorage();
    setHydrated(true);
  }, []);

  // Only redirect after storage has been read — avoids a false unauthenticated flash
  useEffect(() => {
    if (hydrated && !isAuthenticated) {
      router.push('/auth');
    }
  }, [hydrated, isAuthenticated, router]);

  // Show nothing until we know auth state
  if (!hydrated || !isAuthenticated) {
    return <div className="min-h-screen bg-neutral-900" />;
  }

  return <LandingPage />;
}
