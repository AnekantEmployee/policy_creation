import apiClient from './client';
import type { SystemStatus } from '@/types';

export const statusApi = {
  /** GET /status */
  get: async (): Promise<SystemStatus> => {
    const { data } = await apiClient.get<SystemStatus>('/status');
    return data;
  },

  /** GET /health */
  health: async (): Promise<boolean> => {
    try {
      await apiClient.get('/health', { timeout: 3000 });
      return true;
    } catch {
      return false;
    }
  },
};
