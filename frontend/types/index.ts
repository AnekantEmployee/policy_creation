// ─── Framework Types ──────────────────────────────────────────────────────────
export interface Framework {
  id: string;
  name: string;
  icon: string;
  color: string;
  region: string;
  description: string;
  applies_to: string[];
  industries: string[];
  triggers: string[];
  key_articles: string[];
  max_fine: string;
  notification_window: string;
}

export interface FrameworkMatch {
  id: string;
  name: string;
  icon: string;
  color: string;
  region: string;
  description: string;
  relevance_score: number;
  relevance_reason: string;
  is_mandatory: boolean;
  max_fine: string;
  notification_window: string;
}

// ─── Organization / Profiling ─────────────────────────────────────────────────
export interface Organization {
  id: string;
  name: string;
  description: string;
  website?: string;
  country?: string;
  org_type: string;
  industries: string[];
  regions: string[];
  created_at: string;
}

export interface OrgProfileRequest {
  description: string;
  website?: string;
  country?: string;
  employee_count?: string;
  revenue?: string;
}

export interface OrgProfileResponse {
  org_description: string;
  org_type: string;
  industries_detected: string[];
  regions_detected: string[];
  recommended_frameworks: FrameworkMatch[];
  analysis_summary: string;
  timestamp: string;
  session_id?: number;
}

// ─── Policy Types ─────────────────────────────────────────────────────────────
export interface Policy {
  id: string;
  policy_id: string;
  framework: string;
  policy_type: string;
  title: string;
  version: string;
  effective_date: string;
  review_date: string;
  sections: PolicySection[];
  applicable_to: string;
  owner: string;
  classification: string;
  created_at: string;
}

export interface PolicySection {
  title: string;
  content: string;
  references: string[];
}

export interface GeneratedPolicy {
  policy_id: string;
  framework: string;
  policy_type: string;
  title: string;
  version: string;
  effective_date: string;
  review_date: string;
  sections: PolicySection[];
  applicable_to: string;
  owner: string;
  classification: string;
}

export interface PolicyGenerationRequest {
  org_description: string;
  org_name?: string;
  framework: string;
  policy_types: string[];
  org_context?: Record<string, string>;
  personalization_data?: Record<string, string>;
}

export interface PolicyGenerationResponse {
  org_name: string;
  framework: string;
  policies: GeneratedPolicy[];
  summary: string;
  timestamp: string;
}

// ─── Procedure Types ──────────────────────────────────────────────────────────
export interface ProcedureStep {
  step_number: number;
  title: string;
  description: string;
  responsible_role: string;
  timeline: string;
  tools_required: string[];
  documentation: string;
}

export interface GeneratedProcedure {
  procedure_id: string;
  framework: string;
  procedure_type: string;
  title: string;
  purpose: string;
  scope: string;
  steps: ProcedureStep[];
  frequency: string;
  owner: string;
  escalation_path: string;
}

export interface ProcedureGenerationRequest {
  org_description: string;
  org_name?: string;
  framework: string;
  procedure_types: string[];
  org_context?: Record<string, string>;
  personalization_data?: Record<string, string>;
}

export interface ProcedureGenerationResponse {
  org_name: string;
  framework: string;
  procedures: GeneratedProcedure[];
  summary: string;
  timestamp: string;
}

// ─── History Types ────────────────────────────────────────────────────────────
export interface HistorySession {
  session_id: number;
  org_id: number;
  org_name: string;
  org_description: string;
  org_country: string | null;
  org_website: string | null;
  industries: string[];
  regions: string[];
  summary: string;
  selected_frameworks: string[];
  recommended_frameworks: FrameworkMatch[];
  personalization?: Record<string, string>;
  policy_count: number;
  procedure_count: number;
  created_at: string;
}

export interface SessionDetail {
  session_id: number;
  org_name: string;
  org_description: string;
  org_country: string | null;
  org_website: string | null;
  industries: string[];
  regions: string[];
  summary: string;
  selected_frameworks: string[];
  recommended_frameworks: FrameworkMatch[];
  created_at: string;
  policies: GeneratedPolicy[];
  procedures: GeneratedProcedure[];
}

// ─── System Status ────────────────────────────────────────────────────────────
export interface SystemStatus {
  status: string;
  groq_keys: number;
  groq_models: string[];
  groq_total_slots: number;
  tavily_available: boolean;
  supported_frameworks: string[];
  version: string;
}

// ─── Wizard State ─────────────────────────────────────────────────────────────
export type WizardPhase =
  | 'org_info'
  | 'analyzing'
  | 'frameworks'
  | 'doc_types'
  | 'conv_personalize'
  | 'generating'
  | 'done';

export interface PersonalizationQuestion {
  key: string;
  label: string;
  hint: string;
  type: 'text' | 'email' | 'phone' | 'textarea' | 'select';
  options?: string[];
  category: 'contacts' | 'tools' | 'roles' | 'processes' | 'legal' | 'technical';
}
