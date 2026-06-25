import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  timeout: 120_000, // AI generation can take 1-2 min
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach authorization header
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (err) => Promise.reject(err)
);

// Global error interceptor — backend returns plain models, not wrapped responses
apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail;
    if (detail) err.message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    return Promise.reject(err);
  }
);

export default apiClient;
