import { useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

/**
 * Hook to manage authentication and protected route access
 * Initializes auth from storage on mount and handles token refresh
 */
export function useAuth() {
  const router = useRouter();
  const { isAuthenticated, user, accessToken, refreshAccessToken, initializeFromStorage, clearAuth } =
    useAuthStore();

  // Track whether we've done the first hydration
  const hydratedRef = useRef(false);

  // Initialize auth from storage on mount (once)
  useEffect(() => {
    if (!hydratedRef.current) {
      hydratedRef.current = true;
      initializeFromStorage();
    }
  }, [initializeFromStorage]);

  // Set up token refresh interval (refresh 5 minutes before expiry)
  // Only runs after hydration — avoids false redirect on first load
  useEffect(() => {
    if (!isAuthenticated || !accessToken) return;

    const refreshInterval = setInterval(async () => {
      const refreshed = await refreshAccessToken();
      if (!refreshed) {
        router.push('/auth');
      }
    }, 25 * 60 * 1000); // 25 minutes

    return () => clearInterval(refreshInterval);
  }, [isAuthenticated, accessToken, refreshAccessToken, router]);

  // Function to require authentication
  const requireAuth = useCallback(() => {
    if (!isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, router]);

  return {
    isAuthenticated,
    user,
    requireAuth,
    clearAuth,
  };
}

/**
 * Hook to protect a route - redirects to auth if not authenticated
 */
export function useProtectedRoute() {
  const { isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, router]);

  return isAuthenticated;
}
