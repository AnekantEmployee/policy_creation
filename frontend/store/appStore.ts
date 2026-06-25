import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Organization, Policy } from '@/types';

interface AppState {
  currentOrganization: Organization | null;
  setCurrentOrganization: (org: Organization | null) => void;

  policies: Policy[];
  setPolicies: (policies: Policy[]) => void;
  addPolicy: (policy: Policy) => void;
  updatePolicy: (policy: Policy) => void;
  removePolicy: (policyId: string) => void;

  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;

  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      currentOrganization: null,
      setCurrentOrganization: (org) => set({ currentOrganization: org }),

      policies: [],
      setPolicies: (policies) => set({ policies }),
      addPolicy: (policy) => set((s) => ({ policies: [...s.policies, policy] })),
      updatePolicy: (policy) =>
        set((s) => ({ policies: s.policies.map((p) => (p.id === policy.id ? policy : p)) })),
      removePolicy: (policyId) =>
        set((s) => ({ policies: s.policies.filter((p) => p.id !== policyId) })),

      isLoading: false,
      setIsLoading: (loading) => set({ isLoading: loading }),

      sidebarOpen: false,
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
    }),
    {
      name: 'app-store',
      version: 1,
      migrate: (persistedState, version) => {
        // Return the persisted state as-is for any older version;
        // add field-by-field migrations here if the state shape changes.
        return persistedState as AppState;
      },
      partialize: (state) => ({ sidebarOpen: state.sidebarOpen }),
    }
  )
);
