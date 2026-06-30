'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { BotBubble, UserBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';
import { ChevronRight } from 'lucide-react';

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

interface FrameworkConfig {
  policies: string[];
  procedures: string[];
}

export const ChatDocTypes: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const { selectedFrameworks, selectedPolicyTypes, selectedProcedureTypes, setDocTypes, setPhase, reset } = useWizardStore();

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

  // Toggle policy for current framework
  const togglePolicy = (k: string) => {
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

  // Toggle procedure for current framework
  const toggleProcedure = (k: string) => {
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

  const handleConfirm = () => {
    // Collect all unique policies and procedures across frameworks
    const allPolicies = new Set<string>();
    const allProcedures = new Set<string>();
    
    Object.values(frameworkConfigs).forEach(config => {
      config.policies.forEach(p => allPolicies.add(p));
      config.procedures.forEach(p => allProcedures.add(p));
    });

    if (allPolicies.size === 0 && allProcedures.size === 0) return;
    
    // Pass per-framework configs into store so generation can use them
    setDocTypes(Array.from(allPolicies), Array.from(allProcedures), selectedFrameworks, frameworkConfigs);
    setPhase('conv_personalize');
  };

  const handleBack = () => setPhase('frameworks');
  const handleExit = () => {
    reset();
    router.push('/');
  };

  if (done) {
    const totalPolicies = new Set<string>();
    const totalProcedures = new Set<string>();
    Object.values(frameworkConfigs).forEach(config => {
      config.policies.forEach(p => totalPolicies.add(p));
      config.procedures.forEach(p => totalProcedures.add(p));
    });

    return (
      <ChatGroup>
        <BotBubble done>Document types selected.</BotBubble>
        <UserBubble>
          {totalPolicies.size > 0 && <span>{totalPolicies.size} policies</span>}
          {totalPolicies.size > 0 && totalProcedures.size > 0 && ' · '}
          {totalProcedures.size > 0 && <span>{totalProcedures.size} procedures</span>}
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

  const currentConfig = frameworkConfigs[activeFramework] || { policies: [], procedures: [] };

  return (
    <ChatGroup>
      <BotBubble>
        <p>Customize which documents to generate for each framework.</p>
      </BotBubble>

      <div className="ml-11 space-y-4 bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 max-w-2xl">

        {/* Framework tabs */}
        {selectedFrameworks.length > 1 && (
          <div>
            <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">📊 Select Framework</p>
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
            <div className="text-xs text-neutral-500 mt-2">
              Configuring: <strong>{activeFramework}</strong>
            </div>
          </div>
        )}

        {/* Single framework notice */}
        {selectedFrameworks.length === 1 && (
          <div className="text-xs text-neutral-500 pb-2">
            Framework: <strong>{activeFramework}</strong>
          </div>
        )}

        {/* Policy types for active framework */}
        <div>
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
            📋 Policies for {activeFramework} <span className="normal-case font-normal text-neutral-400">({currentConfig.policies.length} selected)</span>
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(POLICY_TYPES).map(([k, label]) => (
              <button
                key={k}
                onClick={() => togglePolicy(k)}
                className={`text-left px-2.5 py-2 text-xs rounded-lg border transition-all ${
                  currentConfig.policies.includes(k)
                    ? 'border-primary-400 bg-primary-50 text-primary-800 font-medium'
                    : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'
                }`}
              >
                {currentConfig.policies.includes(k) ? '✓ ' : ''}{label}
              </button>
            ))}
          </div>
        </div>

        {/* Procedure types for active framework */}
        <div>
          <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
            ⚙️ Procedures for {activeFramework} <span className="normal-case font-normal text-neutral-400">({currentConfig.procedures.length} selected)</span>
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {Object.entries(PROCEDURE_TYPES).map(([k, label]) => (
              <button
                key={k}
                onClick={() => toggleProcedure(k)}
                className={`text-left px-2.5 py-2 text-xs rounded-lg border transition-all ${
                  currentConfig.procedures.includes(k)
                    ? 'border-secondary-400 bg-secondary-50 text-secondary-800 font-medium'
                    : 'border-neutral-200 text-neutral-600 hover:border-neutral-300'
                }`}
              >
                {currentConfig.procedures.includes(k) ? '✓ ' : ''}{label}
              </button>
            ))}
          </div>
        </div>

        {/* Summary of all frameworks */}
        {selectedFrameworks.length > 1 && (
          <div className="bg-neutral-50 rounded-lg p-3 space-y-1.5">
            <p className="text-xs font-semibold text-neutral-600">📊 Summary:</p>
            <div className="space-y-1">
              {selectedFrameworks.map(fw => (
                <div key={fw} className="text-xs text-neutral-600">
                  <strong>{fw}:</strong> {frameworkConfigs[fw]?.policies?.length || 0} policies, {frameworkConfigs[fw]?.procedures?.length || 0} procedures
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-2">
          <button
            onClick={handleConfirm}
            disabled={Object.values(frameworkConfigs).every(c => c.policies.length === 0 && c.procedures.length === 0)}
            className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity shadow-sm"
          >
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
