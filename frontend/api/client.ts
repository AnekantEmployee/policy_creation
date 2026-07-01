import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://10.4.32.170:8001',
  timeout: 120_000, // AI generation can take 1-2 min
  headers: { 'Content-Type': 'application/json' },
});

// Track if we're currently refreshing to avoid concurrent refresh requests
let isRefreshing = false;
let failedQueue: Array<{ resolve: (token: string) => void; reject: (err: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token!);
    }
  });
  failedQueue = [];
};

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

// Response interceptor — handle 401 errors and refresh token
apiClient.interceptors.response.use(
  (res) => res,
  async (err) => {
    const detail = err?.response?.data?.detail;
    if (detail) err.message = typeof detail === 'string' ? detail : JSON.stringify(detail);

    // If 401 (token expired) and not already refreshing, attempt to refresh
    if (err.response?.status === 401 && typeof window !== 'undefined' && !isRefreshing) {
      isRefreshing = true;
      const refreshToken = localStorage.getItem('refresh_token');

      if (refreshToken) {
        try {
          // Import here to avoid circular dependencies
          const { useAuthStore } = await import('@/store/authStore');
          const refreshed = await useAuthStore.getState().refreshAccessToken();

          if (refreshed) {
            processQueue(null, localStorage.getItem('access_token'));
            isRefreshing = false;

            // Retry original request with new token
            const originalConfig = err.config;
            const newToken = localStorage.getItem('access_token');
            if (newToken) {
              originalConfig.headers.Authorization = `Bearer ${newToken}`;
              return apiClient(originalConfig);
            }
          } else {
            processQueue(new Error('Token refresh failed'), null);
            isRefreshing = false;
          }
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          isRefreshing = false;
        }
      } else {
        isRefreshing = false;
      }
    } else if (err.response?.status === 401 && isRefreshing) {
      // Queue the request if refresh is in progress
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      }).then((token) => {
        const originalConfig = err.config;
        originalConfig.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalConfig);
      });
    }

    return Promise.reject(err);
  }
);

export default apiClient;
