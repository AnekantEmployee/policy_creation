import apiClient from './client';
import type { PolicyGenerationRequest, PolicyGenerationResponse } from '@/types';

export interface PolicyGenerationRequestWithSession extends PolicyGenerationRequest {
  session_id?: number | null;
}

export const policiesApi = {
  /** POST /policies/generate */
  generate: async (req: PolicyGenerationRequestWithSession): Promise<PolicyGenerationResponse> => {
    const { data } = await apiClient.post<PolicyGenerationResponse>('/policies/generate', req);
    return data;
  },
};
