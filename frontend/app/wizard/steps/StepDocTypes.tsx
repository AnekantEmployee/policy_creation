'use client';

import React, { useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { Button } from '@/app/components/Button';
import { FileText, Zap } from 'lucide-react';

const POLICY_TYPES: Record<string, string> = {
  data_protection: 'Data Protection & Privacy',
  incident_response: 'Incident Response',
  access_control: 'Access Control & IAM',
  data_retention: 'Data Retention & Disposal',
  third_party_risk: 'Third-Party Risk Management',
  acceptable_use: 'Acceptable Use',
  business_continuity: 'Business Continuity & DR',
  encryption: 'Encryption & Key Management',
};

const PROCEDURE_TYPES: Record<string, string> = {
  incident_response: 'Security Incident Response',
  data_breach: 'Data Breach Notification',
  access_review: 'Periodic Access Review',
  vendor_assessment: 'Vendor Due Diligence',
  data_subject_request: 'Data Subject Rights Request',
  risk_assessment: 'Risk Assessment',
  backup_recovery: 'Backup & Recovery Testing',
  security_awareness: 'Security Awareness Training',
  change_management: 'Change Management',
  vulnerability_management: 'Vulnerability Management',
};

const TypeToggle: React.FC<{ label: string; selected: boolean; onClick: () => void }> = ({ label, selected, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    className={`text-left px-3 py-2 rounded-lg text-sm border transition-all duration-200 ${
      selected
        ? 'bg-primary-600 text-white border-primary-600 font-medium'
        : 'bg-white text-neutral-700 border-neutral-200 hover:border-primary-400'
    }`}
  >
    {label}
  </button>
);

export const StepDocTypes: React.FC = () => {
  const { selectedFrameworks, selectedPolicyTypes, selectedProcedureTypes, setDocTypes, setPhase } = useWizardStore();

  const [policies, setPolicies]     = useState<string[]>(selectedPolicyTypes);
  const [procedures, setProcedures] = useState<string[]>(selectedProcedureTypes);
  const [genFw, setGenFw]           = useState<string[]>(selectedFrameworks.slice(0, 2));

  const togglePol = (k: string) => setPolicies((p) => p.includes(k) ? p.filter((x) => x !== k) : [...p, k]);
  const toggleProc = (k: string) => setProcedures((p) => p.includes(k) ? p.filter((x) => x !== k) : [...p, k]);
  const toggleFw = (k: string) => setGenFw((p) => p.includes(k) ? p.filter((x) => x !== k) : [...p, k]);

  const handleNext = () => {
    if (!policies.length && !procedures.length) return;
    if (!genFw.length) return;
    setDocTypes(policies, procedures, genFw);
    setPhase('personalizing');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-neutral-900">Choose Documents to Generate</h2>
        <p className="text-sm text-neutral-500 mt-1">Select which policies and procedures you need.</p>
      </div>

      {/* Framework selector */}
      <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
        <h3 className="text-sm font-semibold text-neutral-700">Generate for which frameworks?</h3>
        <div className="flex flex-wrap gap-2">
          {selectedFrameworks.map((fw) => (
            <TypeToggle key={fw} label={fw} selected={genFw.includes(fw)} onClick={() => toggleFw(fw)} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Policies */}
        <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary-600" />
            <h3 className="text-sm font-semibold text-neutral-700">Policies ({policies.length} selected)</h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(POLICY_TYPES).map(([k, v]) => (
              <TypeToggle key={k} label={v} selected={policies.includes(k)} onClick={() => togglePol(k)} />
            ))}
          </div>
        </div>

        {/* Procedures */}
        <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-secondary-600" />
            <h3 className="text-sm font-semibold text-neutral-700">Procedures ({procedures.length} selected)</h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(PROCEDURE_TYPES).map(([k, v]) => (
              <TypeToggle key={k} label={v} selected={procedures.includes(k)} onClick={() => toggleProc(k)} />
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button
          variant="primary"
          size="lg"
          disabled={(!policies.length && !procedures.length) || !genFw.length}
          onClick={handleNext}
        >
          Next: Personalize →
        </Button>
      </div>
    </div>
  );
};
