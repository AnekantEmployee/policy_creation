'use client';

import React from 'react';
import { useWizardStore } from '@/store/wizardStore';

const STEPS = [
  { label: 'Org Info',      phases: ['org_info'] },
  { label: 'Frameworks',    phases: ['analyzing', 'frameworks'] },
  { label: 'Doc Types',     phases: ['doc_types'] },
  { label: 'Personalise',   phases: ['conv_personalize'] },
  { label: 'Generate',      phases: ['generating', 'done'] },
];

export const ProgressBar: React.FC = () => {
  const phase = useWizardStore((s) => s.phase);
  const current = STEPS.findIndex((s) => s.phases.includes(phase));

  return (
    <div className="mb-8">
      <div className="flex items-center gap-0">
        {STEPS.map((step, i) => {
          const done    = i < current;
          const active  = i === current;

          return (
            <React.Fragment key={step.label}>
              <div className="flex flex-col items-center gap-1.5 min-w-0">
                <div className={`h-7 w-7 rounded-full text-xs font-bold flex items-center justify-center transition-all duration-300 ${
                  done   ? 'bg-primary-600 text-white' :
                  active ? 'bg-primary-600 text-white ring-4 ring-primary-100' :
                           'bg-neutral-200 text-neutral-400'
                }`}>
                  {done ? '✓' : i + 1}
                </div>
                <span className={`text-xs font-medium hidden sm:block ${
                  active ? 'text-primary-600' : done ? 'text-neutral-600' : 'text-neutral-400'
                }`}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className={`flex-1 h-0.5 mx-1 mb-5 sm:mb-0 sm:mx-2 rounded transition-all duration-300 ${
                  i < current ? 'bg-primary-600' : 'bg-neutral-200'
                }`} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
