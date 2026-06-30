'use client';

import React, { useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { Button } from '@/app/components/Button';
import { FileText, Zap, ChevronRight } from 'lucide-react';

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

interface FrameworkConfig {
  policies: string[];
  procedures: string[];
}

export const StepDocTypes: React.FC = () => {
  const { selectedFrameworks, selectedPolicyTypes, selectedProcedureTypes, setDocTypes, setPhase } = useWizardStore();

  // Track selections per framework
  const [frameworkConfigs, setFrameworkConfigs] = useState<Record<string, FrameworkConfig>>(() => {
    const initial: Record<string, FrameworkConfig> = {};
    selectedFrameworks.forEach(fw => {
      initial[fw] = {
        policies: selectedPolicyTypes,
        procedures: selectedProcedureTypes,
      };
    });
    return initial;
  });

  const [activeFramework, setActiveFramework] = useState<string>(selectedFrameworks[0] || '');

  const togglePol = (k: string) => {
    setFrameworkConfigs(prev => ({
      ...prev,
      [activeFramework]: {
        ...prev[activeFramework],
        policies: prev[activeFramework].policies.includes(k)
          ? prev[activeFramework].policies.filter(x => x !== k)
          : [...prev[activeFramework].policies, k],
      },
    }));
  };

  const toggleProc = (k: string) => {
    setFrameworkConfigs(prev => ({
      ...prev,
      [activeFramework]: {
        ...prev[activeFramework],
        procedures: prev[activeFramework].procedures.includes(k)
          ? prev[activeFramework].procedures.filter(x => x !== k)
          : [...prev[activeFramework].procedures, k],
      },
    }));
  };

  const handleNext = () => {
    // Collect all unique policies and procedures across frameworks
    const allPolicies = new Set<string>();
    const allProcedures = new Set<string>();
    
    Object.values(frameworkConfigs).forEach(config => {
      config.policies.forEach(p => allPolicies.add(p));
      config.procedures.forEach(p => allProcedures.add(p));
    });

    if (allPolicies.size === 0 && allProcedures.size === 0) return;
    
    setDocTypes(Array.from(allPolicies), Array.from(allProcedures), selectedFrameworks);
    setPhase('conv_personalize');
  };

  const currentConfig = frameworkConfigs[activeFramework] || { policies: [], procedures: [] };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-neutral-900">Choose Documents to Generate</h2>
        <p className="text-sm text-neutral-500 mt-1">Customize policies and procedures for each framework.</p>
      </div>

      {/* Framework selector */}
      {selectedFrameworks.length > 1 && (
        <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
          <h3 className="text-sm font-semibold text-neutral-700">📊 Select Framework to Configure</h3>
          <div className="flex flex-wrap gap-2">
            {selectedFrameworks.map(fw => (
              <button
                key={fw}
                onClick={() => setActiveFramework(fw)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg border-2 transition-all flex items-center gap-1 ${
                  activeFramework === fw
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'
                }`}
              >
                {activeFramework === fw && <ChevronRight className="h-3.5 w-3.5" />}
                {fw}
              </button>
            ))}
          </div>
          <div className="text-xs text-neutral-500">
            Configuring: <strong>{activeFramework}</strong>
          </div>
        </div>
      )}

      {selectedFrameworks.length === 1 && (
        <div className="text-xs text-neutral-500 bg-neutral-50 rounded-lg p-3">
          Framework: <strong>{activeFramework}</strong>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Policies */}
        <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary-600" />
            <h3 className="text-sm font-semibold text-neutral-700">
              Policies for {activeFramework} ({currentConfig.policies.length} selected)
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(POLICY_TYPES).map(([k, v]) => (
              <TypeToggle key={k} label={v} selected={currentConfig.policies.includes(k)} onClick={() => togglePol(k)} />
            ))}
          </div>
        </div>

        {/* Procedures */}
        <div className="bg-white rounded-xl border border-neutral-200 p-5 space-y-3">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-secondary-600" />
            <h3 className="text-sm font-semibold text-neutral-700">
              Procedures for {activeFramework} ({currentConfig.procedures.length} selected)
            </h3>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {Object.entries(PROCEDURE_TYPES).map(([k, v]) => (
              <TypeToggle key={k} label={v} selected={currentConfig.procedures.includes(k)} onClick={() => toggleProc(k)} />
            ))}
          </div>
        </div>
      </div>

      {/* Summary for multiple frameworks */}
      {selectedFrameworks.length > 1 && (
        <div className="bg-neutral-50 rounded-xl border border-neutral-200 p-4 space-y-2">
          <p className="text-xs font-semibold text-neutral-700">📊 Summary:</p>
          <div className="space-y-1">
            {selectedFrameworks.map(fw => (
              <div key={fw} className="text-xs text-neutral-600">
                <strong>{fw}:</strong> {frameworkConfigs[fw]?.policies?.length || 0} policies, {frameworkConfigs[fw]?.procedures?.length || 0} procedures
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex justify-end">
        <Button
          variant="primary"
          size="lg"
          disabled={Object.values(frameworkConfigs).every(c => c.policies.length === 0 && c.procedures.length === 0)}
          onClick={handleNext}
        >
          Next: Personalize →
        </Button>
      </div>
    </div>
  );
};
