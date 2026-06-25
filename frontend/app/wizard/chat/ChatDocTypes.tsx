'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { BotBubble, UserBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';

const POLICY_TYPES: Record<string, string> = {
  data_protection:    'Data Protection & Privacy',
  incident_response:  'Incident Response',
  access_control:     'Access Control & IAM',
  data_retention:     'Data Retention & Disposal',
  third_party_risk:   'Third-Party Risk Management',
  acceptable_use:     'Acceptable Use',
  business_continuity:'Business Continuity & DR',
  encryption:         'Encryption & Key Management',
};

const PROCEDURE_TYPES: Record<string, string> = {
  incident_response:     'Security Incident Response',
  data_breach:           'Data Breach Notification',
  access_review:         'Periodic Access Review',
  vendor_assessment:     'Vendor Due Diligence',
  data_subject_request:  'Data Subject Rights Request',
  risk_assessment:       'Risk Assessment',
  backup_recovery:       'Backup & Recovery Testing',
  security_awareness:    'Security Awareness Training',
  change_management:     'Change Management',
  vulnerability_management: 'Vulnerability Management',
};

interface Props { active: boolean; done: boolean; }

export const ChatDocTypes: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const { selectedFrameworks, selectedPolicyTypes, selectedProcedureTypes, setDocTypes, setPhase, reset } = useWizardStore();

  const [pols,  setPols]  = useState<string[]>(selectedPolicyTypes);
  const [procs, setProcs] = useState<string[]>(selectedProcedureTypes);
  const [fws,   setFws]   = useState<string[]>(selectedFrameworks.slice(0, 1));

  const togglePol  = (k: string) => setPols(p  => p.includes(k)  ? p.filter(x=>x!==k)  : [...p, k]);
  const toggleProc = (k: string) => setProcs(p => p.includes(k)  ? p.filter(x=>x!==k)  : [...p, k]);
  const toggleFw   = (k: string) => setFws(p   => p.includes(k)  ? p.filter(x=>x!==k)  : [...p, k]);

  const handleConfirm = () => {
    if (pols.length === 0 && procs.length === 0) return;
    if (fws.length === 0) return;
    setDocTypes(pols, procs, fws);
    setPhase('personalizing');
  };

  const handleBack = () => setPhase('frameworks');
  const handleExit = () => {
    reset();
    router.push('/');
  };

  if (done) {
    return (
      <ChatGroup>
        <BotBubble done>Document types selected.</BotBubble>
        <UserBubble>
          {selectedPolicyTypes.length > 0 && <span>{selectedPolicyTypes.length} policies</span>}
          {selectedPolicyTypes.length > 0 && selectedProcedureTypes.length > 0 && ' · '}
          {selectedProcedureTypes.length > 0 && <span>{selectedProcedureTypes.length} procedures</span>}
          {' for '}{selectedFrameworks.slice(0,2).join(', ')}
        </UserBubble>
        {active && (
          <ChatNavigation
            onBack={handleBack}
            onExit={handleExit}
            canGoBack={true}
          />
        )}
      </ChatGroup>
    );
  }

  if (!active) return null;

  return (
    <ChatGroup>
      <BotBubble>
        <p>Which document types do you want to generate, and for which frameworks?</p>
      </BotBubble>

      <div className="ml-11 space-y-4 bg-white rounded-2xl border border-neutral-200 shadow-sm p-5">

        {/* Framework selection for generation */}
        <div>
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">Generate for Frameworks</p>
          <div className="flex flex-wrap gap-2">
            {selectedFrameworks.map(fw => (
              <button key={fw} onClick={() => toggleFw(fw)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg border-2 transition-all ${fws.includes(fw) ? 'border-primary-500 bg-primary-50 text-primary-700' : 'border-neutral-200 text-neutral-500 hover:border-neutral-300'}`}>
                {fws.includes(fw) ? '✓ ' : ''}{fw}
              </button>
            ))}
          </div>
        </div>

        {/* Policy types */}
        <div>
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">Policy Types <span className="normal-case font-normal text-neutral-400">({pols.length} selected)</span></p>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(POLICY_TYPES).map(([k, label]) => (
              <button key={k} onClick={() => togglePol(k)}
                className={`text-left px-2.5 py-2 text-xs rounded-lg border transition-all ${pols.includes(k) ? 'border-primary-400 bg-primary-50 text-primary-800 font-medium' : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'}`}>
                {pols.includes(k) ? '✓ ' : ''}{label}
              </button>
            ))}
          </div>
        </div>

        {/* Procedure types */}
        <div>
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">Procedure Types <span className="normal-case font-normal text-neutral-400">({procs.length} selected)</span></p>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(PROCEDURE_TYPES).map(([k, label]) => (
              <button key={k} onClick={() => toggleProc(k)}
                className={`text-left px-2.5 py-2 text-xs rounded-lg border transition-all ${procs.includes(k) ? 'border-secondary-400 bg-secondary-50 text-secondary-800 font-medium' : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'}`}>
                {procs.includes(k) ? '✓ ' : ''}{label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <button
            onClick={handleConfirm}
            disabled={(pols.length === 0 && procs.length === 0) || fws.length === 0}
            className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity shadow-sm">
            Next: Personalize Details →
          </button>
          <ChatNavigation
            onBack={handleBack}
            onExit={handleExit}
            canGoBack={true}
          />
        </div>
      </div>
    </ChatGroup>
  );
};
