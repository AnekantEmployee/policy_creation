'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { policiesApi } from '@/api/policies';
import { proceduresApi } from '@/api/procedures';
import { BotBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';
import toast from 'react-hot-toast';
import type { GeneratedPolicy, GeneratedProcedure } from '@/types';

interface Props { active: boolean; done: boolean; }

export const ChatGenerating: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const {
    orgDescription, orgName, sessionId,
    selectedGenFrameworks, selectedPolicyTypes, selectedProcedureTypes,
    frameworkDocConfigs, convPersonalizeAnswers, answers,
    setResults, setPhase, reset,
  } = useWizardStore();

  const [log, setLog] = useState<string[]>([]);
  const addLog = (msg: string) => setLog(p => [...p, msg]);

  const handleExit = () => {
    reset();
    router.push('/');
  };

  useEffect(() => {
    if (!active) return;

    const generate = async () => {
      // Merge answers from both structured Q&A and conversational personalization
      const orgContext: Record<string, string> = {
        org_name: orgName,
        org_description: orgDescription,
        ...answers,
        ...convPersonalizeAnswers,
      };
      const allPolicies:   GeneratedPolicy[]   = [];
      const allProcedures: GeneratedProcedure[] = [];

      for (const fw of selectedGenFrameworks) {
        // Use per-framework config if available, fall back to global selections
        const fwConfig = frameworkDocConfigs[fw];
        const policyTypes   = fwConfig ? fwConfig.policies   : selectedPolicyTypes;
        const procedureTypes = fwConfig ? fwConfig.procedures : selectedProcedureTypes;

        if (policyTypes.length > 0) {
          addLog(`Generating ${policyTypes.length} policies for ${fw}…`);
          try {
            const res = await policiesApi.generate({
              org_description: orgDescription,
              org_name: orgName || 'Your Organization',
              framework: fw,
              policy_types: policyTypes,
              org_context: orgContext,
              session_id: sessionId,
            });
            allPolicies.push(...res.policies);
            addLog(`✓ ${res.policies.length} ${fw} policies done`);
          } catch {
            addLog(`✗ ${fw} policies failed`);
            toast.error(`${fw} policy generation failed`);
          }
        }
        if (procedureTypes.length > 0) {
          addLog(`Generating ${procedureTypes.length} procedures for ${fw}…`);
          try {
            const res = await proceduresApi.generate({
              org_description: orgDescription,
              org_name: orgName || 'Your Organization',
              framework: fw,
              procedure_types: procedureTypes,
              org_context: orgContext,
              session_id: sessionId,
            });
            allProcedures.push(...res.procedures);
            addLog(`✓ ${res.procedures.length} ${fw} procedures done`);
          } catch {
            addLog(`✗ ${fw} procedures failed`);
          }
        }
      }

      const seenPol = new Set<string>();
      const seenProc = new Set<string>();
      const uniquePols: typeof allPolicies = [];
      const uniqueProcs: typeof allProcedures = [];
      for (const p of allPolicies)   { if (!seenPol.has(p.policy_id))     { seenPol.add(p.policy_id);     uniquePols.push(p); } }
      for (const p of allProcedures) { if (!seenProc.has(p.procedure_id)) { seenProc.add(p.procedure_id); uniqueProcs.push(p); } }

      setResults(uniquePols, uniqueProcs);
      setPhase('done');
    };

    generate();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  return (
    <ChatGroup>
      <BotBubble>
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <div className="flex gap-1">
              {[0,1,2].map(i => <span key={i} className="h-2 w-2 rounded-full bg-secondary-500 animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
            </div>
            <span className="font-medium">Generating your compliance documents… (1–3 minutes)</span>
          </div>

          {/* Live log */}
          <div className="bg-neutral-900 rounded-xl p-3 text-xs font-mono text-neutral-300 space-y-0.5 max-h-36 overflow-y-auto">
            {log.length === 0 && <span className="text-neutral-500">Starting…</span>}
            {log.map((msg, i) => (
              <div key={i} className={msg.startsWith('✓') ? 'text-green-400' : msg.startsWith('✗') ? 'text-red-400' : 'text-neutral-300'}>
                {msg}
              </div>
            ))}
          </div>
        </div>
      </BotBubble>
      <ChatNavigation
        onExit={handleExit}
      />
    </ChatGroup>
  );
};
