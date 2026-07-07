import apiClient from './client';

/**
 * Request to consolidate policies for a session into a master policy
 */
export interface ConsolidateRequest {
  session_id: number;
  regenerate?: boolean;
}

/**
 * Response from consolidation endpoint
 */
export interface ConsolidateResponse {
  master_policy_id: string;
  title: string;
  frameworks: string[];
  domains_count: number;
  executive_summary?: string;
  created_at?: string;
}

/**
 * A single integrated requirement from the master policy
 */
export interface ConsolidatedRequirement {
  requirement_id: string;
  title: string;
  description: string;
  frameworks: string[];
  framework_references: string[];
  is_mandatory: boolean;
  max_penalty?: string;
  implementation_steps: string[];
  responsibility: string;
}

/**
 * A domain section containing related requirements
 */
export interface ConsolidatedDomain {
  domain_name: string;
  domain_description: string;
  integrated_requirements: ConsolidatedRequirement[];
}

/**
 * A row in the compliance control matrix
 */
export interface ComplianceMatrixRow {
  control_name: string;
  [key: string]: string; // framework name => status (Required, Mandatory, Optional, etc.)
}

/**
 * A phase in the implementation roadmap
 */
export interface ImplementationPhase {
  phase: number;
  duration: string;
  focus: string;
  controls: string[];
}

/**
 * Full master policy response from the API
 */
export interface MasterPolicyResponse {
  master_policy_id: string;
  title: string;
  version: string;
  executive_summary: string;
  aligned_frameworks: string[];
  consolidation_notes: string;
  domains: ConsolidatedDomain[];
  compliance_matrix: ComplianceMatrixRow[];
  implementation_roadmap: ImplementationPhase[];
  created_at?: string;
  updated_at?: string;
}

/**
 * Master Policy API client
 * Handles all master policy related operations
 */
export const masterPolicyApi = {
  /**
   * Consolidate all policies from a session into a single master policy
   * @param req - Consolidation request with session_id and optional regenerate flag
   * @returns Consolidation response with master_policy_id and summary
   */
  consolidate: async (req: ConsolidateRequest): Promise<ConsolidateResponse> => {
    const { data } = await apiClient.post<ConsolidateResponse>(
      '/policies/consolidate',
      req
    );
    return data;
  },

  /**
   * Get the consolidated master policy for a session
   * @param sessionId - Session ID to retrieve master policy for
   * @returns Full master policy with all domains, requirements, and matrices
   */
  get: async (sessionId: number): Promise<MasterPolicyResponse> => {
    const { data } = await apiClient.get<MasterPolicyResponse>(
      `/policies/master/${sessionId}`
    );
    return data;
  },

  /**
   * Export the master policy as a DOCX file
   * @param sessionId - Session ID to export master policy for
   * @returns Blob containing the DOCX file data
   */
  exportDocx: async (sessionId: number): Promise<Blob> => {
    const response = await apiClient.post(
      `/export/master-policy/${sessionId}/docx`,
      {},
      { responseType: 'blob' as const }
    );
    return response.data as Blob;
  },
};
