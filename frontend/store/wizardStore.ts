import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  OrgProfileResponse,
  FrameworkMatch,
  GeneratedPolicy,
  GeneratedProcedure,
  PersonalizationQuestion,
  WizardPhase,
} from '@/types';

// Per-framework doc type config — separate policy/procedure selections per framework
export interface FrameworkDocConfig {
  policies: string[];
  procedures: string[];
}

interface WizardState {
  phase: WizardPhase;
  setPhase: (p: WizardPhase) => void;

  // Step 1 — org info
  orgName: string;
  orgDescription: string;
  orgWebsite: string;
  orgCountry: string;
  setOrgInfo: (info: Partial<{ orgName: string; orgDescription: string; orgWebsite: string; orgCountry: string }>) => void;

  // Step 2 — profiling result
  profile: OrgProfileResponse | null;
  setProfile: (p: OrgProfileResponse) => void;
  sessionId: number | null;

  // Step 3 — framework selection
  selectedFrameworks: string[];
  setSelectedFrameworks: (fw: string[]) => void;
  toggleFramework: (id: string) => void;

  // Step 4 — doc type selection (per-framework config)
  frameworkDocConfigs: Record<string, FrameworkDocConfig>;
  setFrameworkDocConfigs: (configs: Record<string, FrameworkDocConfig>) => void;
  // Legacy flat lists (still used by generation loop)
  selectedPolicyTypes: string[];
  selectedProcedureTypes: string[];
  selectedGenFrameworks: string[];
  setDocTypes: (pol: string[], proc: string[], fw: string[], configs?: Record<string, FrameworkDocConfig>) => void;

  // Step 5 — conversational personalization
  convPersonalizeAnswers: Record<string, string>;   // accumulated extracted info
  convPersonalizeHistory: Array<{ role: 'user' | 'assistant'; content: string }>;
  setConvPersonalizeAnswers: (answers: Record<string, string>) => void;
  setConvPersonalizeHistory: (history: Array<{ role: 'user' | 'assistant'; content: string }>) => void;
  mergeConvPersonalizeAnswers: (newAnswers: Record<string, string>) => void;

  // Step 5 (legacy) — structured personalization questions
  questions: PersonalizationQuestion[];
  answers: Record<string, string>;
  questionIndex: number;
  setQuestions: (q: PersonalizationQuestion[]) => void;
  setAnswer: (key: string, val: string) => void;
  nextQuestion: () => void;
  previousQuestion: () => void;
  removeCurrentAnswer: () => void;

  // Step 6 — results
  policies: GeneratedPolicy[];
  procedures: GeneratedProcedure[];
  setResults: (pol: GeneratedPolicy[], proc: GeneratedProcedure[]) => void;

  // Regenerate — load from a saved session without re-entering org info
  loadFromSession: (sessionId: number, orgName: string, orgDescription: string, frameworks: string[]) => void;

  reset: () => void;
}

const DEFAULT_FRAMEWORK_DOC_CONFIG: FrameworkDocConfig = {
  policies: ['data_protection', 'incident_response', 'access_control'],
  procedures: ['incident_response', 'data_breach', 'access_review'],
};

const DEFAULT: Omit<WizardState,
  'setPhase' | 'setOrgInfo' | 'setProfile' | 'setSelectedFrameworks' | 'toggleFramework' |
  'setFrameworkDocConfigs' | 'setDocTypes' |
  'setConvPersonalizeAnswers' | 'setConvPersonalizeHistory' | 'mergeConvPersonalizeAnswers' |
  'setQuestions' | 'setAnswer' | 'nextQuestion' | 'previousQuestion' | 'removeCurrentAnswer' | 'setResults' |
  'loadFromSession' | 'reset'
> = {
  phase: 'org_info',
  orgName: '', orgDescription: '', orgWebsite: '', orgCountry: '',
  profile: null, sessionId: null,
  selectedFrameworks: [],
  frameworkDocConfigs: {},
  selectedPolicyTypes: ['data_protection', 'incident_response', 'access_control'],
  selectedProcedureTypes: ['incident_response', 'data_breach', 'access_review'],
  selectedGenFrameworks: [],
  convPersonalizeAnswers: {},
  convPersonalizeHistory: [],
  questions: [], answers: {}, questionIndex: 0,
  policies: [], procedures: [],
};

export const useWizardStore = create<WizardState>()(
  persist(
    (set, get) => ({
      ...DEFAULT,
      setPhase: (phase) => set({ phase }),
      setOrgInfo: (info) => set((s) => ({ ...s, ...info })),
      setProfile: (profile) => set({ profile, sessionId: profile.session_id ?? null }),
      setSelectedFrameworks: (selectedFrameworks) => set({ selectedFrameworks }),
      toggleFramework: (id) =>
        set((s) => ({
          selectedFrameworks: s.selectedFrameworks.includes(id)
            ? s.selectedFrameworks.filter((f) => f !== id)
            : [...s.selectedFrameworks, id],
        })),
      setFrameworkDocConfigs: (frameworkDocConfigs) => set({ frameworkDocConfigs }),
      setDocTypes: (selectedPolicyTypes, selectedProcedureTypes, selectedGenFrameworks, configs) =>
        set((s) => ({
          selectedPolicyTypes,
          selectedProcedureTypes,
          selectedGenFrameworks,
          frameworkDocConfigs: configs ?? s.frameworkDocConfigs,
        })),
      setConvPersonalizeAnswers: (convPersonalizeAnswers) => set({ convPersonalizeAnswers }),
      setConvPersonalizeHistory: (convPersonalizeHistory) => set({ convPersonalizeHistory }),
      mergeConvPersonalizeAnswers: (newAnswers) =>
        set((s) => ({ convPersonalizeAnswers: { ...s.convPersonalizeAnswers, ...newAnswers } })),
      setQuestions: (questions) => set({ questions, questionIndex: 0, answers: {} }),
      setAnswer: (key, val) => set((s) => ({ answers: { ...s.answers, [key]: val } })),
      nextQuestion: () => set((s) => ({ questionIndex: s.questionIndex + 1 })),
      previousQuestion: () => set((s) => ({ questionIndex: Math.max(0, s.questionIndex - 1) })),
      removeCurrentAnswer: () =>
        set((s) => {
          if (s.questionIndex > 0 && s.questions.length > 0) {
            const currentQ = s.questions[s.questionIndex];
            if (currentQ) {
              const newAnswers = { ...s.answers };
              delete newAnswers[currentQ.key];
              return { answers: newAnswers, questionIndex: Math.max(0, s.questionIndex - 1) };
            }
          }
          return { questionIndex: Math.max(0, s.questionIndex - 1) };
        }),
      setResults: (policies, procedures) => set({ policies, procedures }),
      loadFromSession: (sessionId, orgName, orgDescription, frameworks) =>
        set({
          ...DEFAULT,
          sessionId,
          orgName,
          orgDescription,
          selectedFrameworks: frameworks,
          selectedGenFrameworks: frameworks,
          phase: 'doc_types',
        }),
      reset: () => set({ ...DEFAULT }),
    }),
    {
      name: 'wizard-store',
      version: 3, // bump to discard old persisted state shape
      migrate: (persistedState) => {
        return persistedState as WizardState;
      },
      partialize: (state) => ({
        orgName: state.orgName,
        orgDescription: state.orgDescription,
        orgWebsite: state.orgWebsite,
        orgCountry: state.orgCountry,
        sessionId: state.sessionId,
        selectedFrameworks: state.selectedFrameworks,
        policies: state.policies,
        procedures: state.procedures,
        // phase intentionally NOT persisted
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.phase = 'org_info';
        }
      },
    }
  )
);
