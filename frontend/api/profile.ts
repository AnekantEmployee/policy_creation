import apiClient from './client';
import type { OrgProfileRequest, OrgProfileResponse } from '@/types';

export interface OrgProfileRequestWithName extends OrgProfileRequest {
  name?: string;
}

export const profileApi = {
  /** POST /profile — run AI org profiler, get framework recommendations */
  analyze: async (req: OrgProfileRequestWithName): Promise<OrgProfileResponse> => {
    const { data } = await apiClient.post<OrgProfileResponse>('/profile', req);
    return data;
  },
};
