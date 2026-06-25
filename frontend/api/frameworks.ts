import apiClient from './client';
import type { Framework } from '@/types';

export const frameworksApi = {
  /** GET /frameworks */
  list: async (): Promise<Framework[]> => {
    const { data } = await apiClient.get<{ frameworks: Framework[] }>('/frameworks');
    return data.frameworks;
  },

  /** GET /frameworks/:id */
  get: async (id: string): Promise<Framework> => {
    const { data } = await apiClient.get<Framework>(`/frameworks/${id}`);
    return data;
  },

  /** GET /policy-types */
  policyTypes: async (): Promise<Record<string, { title: string; description: string }>> => {
    const { data } = await apiClient.get<{ policy_types: Record<string, { title: string; description: string }> }>('/policy-types');
    return data.policy_types;
  },

  /** GET /procedure-types */
  procedureTypes: async (): Promise<Record<string, { title: string; description: string; frequency: string }>> => {
    const { data } = await apiClient.get<{ procedure_types: Record<string, { title: string; description: string; frequency: string }> }>('/procedure-types');
    return data.procedure_types;
  },
};
