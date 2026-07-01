'use client';

import React, { useEffect, useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { policiesApi } from '@/api/policies';
import { proceduresApi } from '@/api/procedures';
import toast from 'react-hot-toast';

export const StepGenerating: React.FC = () => {
  const {
    orgDescription, orgName, sessionId,
    selectedGenFrameworks, selectedPolicyTypes, selectedProcedureTypes,
    answers, convPersonalizeAnswers, setResults, setPhase,
  } = useWizardStore();

  const [progress, setProgress] = useState<string[]>([]);
  const addProgress = (msg: string) => setProgress((p) => [...p, msg]);

  useEffect(() => {
    const generate = async () => {
      const orgContext: Record<string, string> = {
        org_name: orgName,
        org_description: orgDescription,
        ...answers,
        ...convPersonalizeAnswers,
      };

      const allPolicies: NonNullable<ReturnType<typeof useWizardStore.getState>['policies']> = [];
      const allProcedures: NonNullable<ReturnType<typeof useWizardStore.getState>['procedures']> = [];
      const failed: string[] = [];

      for (const fw of selectedGenFrameworks) {
        if (selectedPolicyTypes.length > 0) {
          addProgress(`Generating ${selectedPolicyTypes.length} policies for ${fw}…`);
          try {
            const res = await policiesApi.generate({
              org_description: orgDescription,
              org_name: orgName || 'Your Organization',
              framework: fw,
              policy_types: selectedPolicyTypes,
              org_context: orgContext,
              personalization_data: convPersonalizeAnswers,
              session_id: sessionId,
            });
            allPolicies.push(...res.policies);
            addProgress(`✓ ${res.policies.length} ${fw} policies generated`);
          } catch (e: unknown) {
            const msg = (e as Error).message;
            failed.push(`${fw} policies: ${msg}`);
            addProgress(`✗ ${fw} policies failed`);
          }
        }

        if (selectedProcedureTypes.length > 0) {
          addProgress(`Generating ${selectedProcedureTypes.length} procedures for ${fw}…`);
          try {
            const res = await proceduresApi.generate({
              org_description: orgDescription,
              org_name: orgName || 'Your Organization',
              framework: fw,
              procedure_types: selectedProcedureTypes,
              org_context: orgContext,
              personalization_data: convPersonalizeAnswers,
              session_id: sessionId,
            });
            allProcedures.push(...res.procedures);
            addProgress(`✓ ${res.procedures.length} ${fw} procedures generated`);
          } catch (e: unknown) {
            const msg = (e as Error).message;
            failed.push(`${fw} procedures: ${msg}`);
            addProgress(`✗ ${fw} procedures failed`);
          }
        }
      }

      if (failed.length) toast.error(`Some generations failed. Check results for details.`);

      // Deduplicate by type+framework (IDs can repeat across retries/frameworks)
      const seenPol = new Set<string>();
      const seenProc = new Set<string>();
      const uniquePolicies = allPolicies.filter((p) => {
        const key = `${p.framework}:${p.policy_type}`;
        if (seenPol.has(key)) return false;
        seenPol.add(key); return true;
      });
      const uniqueProcs = allProcedures.filter((p) => {
        const key = `${p.framework}:${p.procedure_type}`;
        if (seenProc.has(key)) return false;
        seenProc.add(key); return true;
      });

      setResults(uniquePolicies, uniqueProcs);
      setPhase('done');
    };

    generate();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-64 gap-6">
      <div className="relative h-16 w-16">
        <div className="absolute inset-0 rounded-full bg-secondary-500/20 animate-ping" />
        <div className="relative h-16 w-16 rounded-full bg-gradient-to-br from-secondary-500 to-primary-600 flex items-center justify-center text-white text-2xl shadow-lg">
          ⚡
        </div>
      </div>

      <div className="text-center">
        <h3 className="text-lg font-semibold text-neutral-900">Generating your compliance documents…</h3>
        <p className="text-sm text-neutral-500 mt-1">This takes 1–3 minutes. AI agents are writing tailored policies and procedures.</p>
      </div>

      {/* Live log */}
      <div className="w-full max-w-md bg-neutral-900 rounded-xl p-4 text-xs font-mono text-neutral-300 space-y-1 max-h-48 overflow-y-auto">
        {progress.map((msg, i) => (
          <div key={i} className={msg.startsWith('✓') ? 'text-green-400' : msg.startsWith('✗') ? 'text-red-400' : 'text-neutral-300'}>
            {msg}
          </div>
        ))}
        {progress.length === 0 && <div className="text-neutral-500">Starting…</div>}
        <div className="h-4 flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <span key={i} className="h-1.5 w-1.5 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      </div>
    </div>
  );
};
