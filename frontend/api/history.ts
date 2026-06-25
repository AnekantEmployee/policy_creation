import apiClient from './client';
import type { HistorySession, SessionDetail, GeneratedPolicy, GeneratedProcedure } from '@/types';

export interface RegenerateRequest {
  frameworks?: string[];
  policy_types?: string[];
  procedure_types?: string[];
  org_context?: Record<string, string>;
}

export interface RegenerateResponse {
  session_id: number;
  org_name: string;
  frameworks: string[];
  policies: GeneratedPolicy[];
  procedures: GeneratedProcedure[];
  policy_count: number;
  procedure_count: number;
}

export const historyApi = {
  /** GET /history?limit=N */
  list: async (limit = 50): Promise<HistorySession[]> => {
    const { data } = await apiClient.get<{ sessions: HistorySession[] }>(`/history?limit=${limit}`);
    return data.sessions;
  },

  /** GET /history/:id */
  get: async (sessionId: number): Promise<SessionDetail> => {
    const { data } = await apiClient.get<SessionDetail>(`/history/${sessionId}`);
    return data;
  },

  /** GET /history/org/:orgName */
  getByOrg: async (orgName: string, limit = 20): Promise<HistorySession[]> => {
    const { data } = await apiClient.get<{ sessions: HistorySession[] }>(
      `/history/org/${encodeURIComponent(orgName)}?limit=${limit}`
    );
    return data.sessions;
  },

  /** POST /history/:id/regenerate */
  regenerate: async (sessionId: number, req: RegenerateRequest): Promise<RegenerateResponse> => {
    const { data } = await apiClient.post<RegenerateResponse>(
      `/history/${sessionId}/regenerate`,
      req
    );
    return data;
  },

  /** PATCH /history/:id/frameworks */
  updateFrameworks: async (sessionId: number, selectedFrameworks: string[]): Promise<void> => {
    await apiClient.patch(`/history/${sessionId}/frameworks`, { selected_frameworks: selectedFrameworks });
  },

  /** DELETE /history/:id */
  delete: async (sessionId: number): Promise<void> => {
    await apiClient.delete(`/history/${sessionId}`);
  },
};
