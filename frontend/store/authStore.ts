import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi, User, AuthResponse } from '@/api/auth';

// ─── Cookie helpers (readable by middleware) ─────────────────────────────────

function setCookie(name: string, value: string, days: number) {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function deleteCookie(name: string) {
  if (typeof document === 'undefined') return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

// ─── Types ───────────────────────────────────────────────────────────────────

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<AuthResponse>;
  signup: (email: string, username: string, password: string, fullName?: string) => Promise<{ status: string; message: string }>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  initializeFromStorage: () => void;
  clearAuth: () => void;
}

// ─── Store ───────────────────────────────────────────────────────────────────

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      isAuthenticated: false,
      user: null,
      accessToken: null,
      refreshToken: null,
      isLoading: false,
      error: null,

      // ── Login ──────────────────────────────────────────────────────────────
      login: async (email, password) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(email, password);

          // Persist tokens
          setCookie('access_token', response.access_token, 1);   // 1 day cookie
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('refresh_token', response.refresh_token);
          localStorage.setItem('user', JSON.stringify(response.user));

          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });

          return response;
        } catch (err: any) {
          const msg = err.message || 'Login failed';
          set({ error: msg, isLoading: false });
          throw err;
        }
      },

      // ── Signup ─────────────────────────────────────────────────────────────
      signup: async (email, username, password, fullName) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authApi.signup({ email, username, password, full_name: fullName });
          set({ isLoading: false });
          return result;
        } catch (err: any) {
          const msg = err.message || 'Signup failed';
          set({ error: msg, isLoading: false });
          throw err;
        }
      },

      // ── Logout ─────────────────────────────────────────────────────────────
      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
        } catch {
          // ignore server errors on logout
        }
        // Always clear client state
        deleteCookie('access_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      },

      // ── Refresh ────────────────────────────────────────────────────────────
      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          get().clearAuth();
          return false;
        }
        try {
          const response = await authApi.refreshToken(refreshToken);
          setCookie('access_token', response.access_token, 1);
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('refresh_token', response.refresh_token);
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            user: response.user,
            isAuthenticated: true,
          });
          return true;
        } catch {
          get().clearAuth();
          return false;
        }
      },

      // ── Hydrate from localStorage (called once on app boot) ────────────────
      initializeFromStorage: () => {
        if (typeof window === 'undefined') return;
        const token = localStorage.getItem('access_token');
        const refresh = localStorage.getItem('refresh_token');
        const raw = localStorage.getItem('user');
        if (token && raw) {
          const user: User = JSON.parse(raw);
          setCookie('access_token', token, 1);   // refresh cookie in case it expired
          set({ accessToken: token, refreshToken: refresh, user, isAuthenticated: true });
        }
      },

      // ── Clear ──────────────────────────────────────────────────────────────
      clearAuth: () => {
        deleteCookie('access_token');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false, error: null });
      },
    }),
    {
      name: 'auth-store',
      version: 1,
      migrate: (persistedState, version) => {
        // Return the persisted state as-is for any older version;
        // add field-by-field migrations here if the state shape changes.
        return persistedState as AuthState;
      },
      // Only persist the user object and isAuthenticated flag across page reloads.
      // Tokens are read back from localStorage inside initializeFromStorage().
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
