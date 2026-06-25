const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  role: 'admin' | 'compliance_officer' | 'security_lead' | 'executive' | 'auditor';
  is_active: boolean;
  is_verified: boolean;
  is_approved: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

async function apiCall<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

function authHeader(): Record<string, string> {
  const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const authApi = {
  login: (email: string, password: string) =>
    apiCall<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  signup: (data: { email: string; username: string; password: string; full_name?: string }) =>
    apiCall<{ id: number; email: string; username: string; status: string; message: string }>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  refreshToken: (refresh_token: string) =>
    apiCall<AuthResponse>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token }),
    }),

  logout: () =>
    apiCall<{ message: string }>('/auth/logout', {
      method: 'POST',
      headers: authHeader(),
    }),

  getCurrentUser: () =>
    apiCall<User>('/auth/me', {
      headers: authHeader(),
    }).catch(() => null),

  changePassword: (old_password: string, new_password: string) =>
    apiCall('/auth/change-password', {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({ old_password, new_password, confirm_password: new_password }),
    }),

  getStoredUser: (): User | null => {
    if (typeof localStorage === 'undefined') return null;
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  },

  isAuthenticated: (): boolean => {
    if (typeof localStorage === 'undefined') return false;
    return !!localStorage.getItem('access_token');
  },
};
