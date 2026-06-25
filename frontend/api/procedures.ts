import apiClient from './client';
import type { ProcedureGenerationRequest, ProcedureGenerationResponse } from '@/types';

export interface ProcedureGenerationRequestWithSession extends ProcedureGenerationRequest {
  session_id?: number | null;
}

export const proceduresApi = {
  /** POST /procedures/generate */
  generate: async (req: ProcedureGenerationRequestWithSession): Promise<ProcedureGenerationResponse> => {
    const { data } = await apiClient.post<ProcedureGenerationResponse>('/procedures/generate', req);
    return data;
  },
};
