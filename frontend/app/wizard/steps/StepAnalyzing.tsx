'use client';

import React, { useEffect } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { profileApi } from '@/api/profile';
import toast from 'react-hot-toast';

export const StepAnalyzing: React.FC = () => {
  const { orgName, orgDescription, orgWebsite, orgCountry, setProfile, setSelectedFrameworks, setPhase } = useWizardStore();

  useEffect(() => {
    const run = async () => {
      try {
        const result = await profileApi.analyze({
          name: orgName || undefined,
          description: orgDescription,
          website: orgWebsite || undefined,
          country: orgCountry || undefined,
        });
        setProfile(result);
        // Pre-select frameworks with ≥70% relevance
        const preSelected = result.recommended_frameworks
          .filter((f) => f.relevance_score >= 0.7)
          .map((f) => f.id);
        setSelectedFrameworks(preSelected);
        setPhase('frameworks');
      } catch (err: unknown) {
        const msg = (err as Error).message ?? 'Analysis failed';
        toast.error(msg);
        setPhase('org_info');
      }
    };
    run();
  }, [orgName, orgDescription, orgWebsite, orgCountry, setProfile, setSelectedFrameworks, setPhase]);

  return (
    <div className="flex flex-col items-center justify-center min-h-64 gap-6 text-center">
      <div className="relative h-16 w-16">
        <div className="absolute inset-0 rounded-full bg-primary-600/20 animate-ping" />
        <div className="relative h-16 w-16 rounded-full bg-gradient-to-br from-primary-600 to-secondary-500 flex items-center justify-center text-white text-2xl shadow-lg">
          🤖
        </div>
      </div>
      <div>
        <h3 className="text-lg font-semibold text-neutral-900">Analyzing your organization…</h3>
        <p className="text-sm text-neutral-500 mt-1">AI agents are identifying applicable compliance frameworks</p>
      </div>
      <div className="flex gap-1.5">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="h-2 w-2 rounded-full bg-primary-500 animate-bounce"
            style={{ animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>
    </div>
  );
};
