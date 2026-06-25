'use client';

import React from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { historyApi } from '@/api/history';
import { Button } from '@/app/components/Button';
import type { FrameworkMatch } from '@/types';

const scoreColor = (s: number) =>
  s >= 0.8 ? 'text-green-600' : s >= 0.6 ? 'text-amber-600' : 'text-red-500';

const FrameworkCard: React.FC<{ fw: FrameworkMatch; selected: boolean; onToggle: () => void }> = ({ fw, selected, onToggle }) => (
  <div
    className={`relative rounded-xl border-2 p-4 cursor-pointer transition-all duration-200 ${
      selected ? 'border-primary-500 bg-primary-50 shadow-md' : 'border-neutral-200 bg-white hover:border-primary-300'
    }`}
    onClick={onToggle}
  >
    {selected && (
      <div className="absolute top-3 right-3 h-5 w-5 rounded-full bg-primary-600 flex items-center justify-center text-white text-xs font-bold">✓</div>
    )}
    <div className="flex items-start gap-3 mb-3">
      <span className="text-2xl">{fw.icon}</span>
      <div className="min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-bold text-neutral-900 text-sm">{fw.id}</span>
          {fw.is_mandatory && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-700 font-semibold">MANDATORY</span>
          )}
        </div>
        <p className="text-xs text-neutral-500 truncate">{fw.name}</p>
      </div>
    </div>

    {/* Score bar */}
    <div className="h-1.5 bg-neutral-200 rounded-full mb-1">
      <div
        className="h-1.5 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500 transition-all duration-500"
        style={{ width: `${fw.relevance_score * 100}%` }}
      />
    </div>
    <div className="flex justify-between items-center mb-2">
      <span className={`text-xs font-semibold ${scoreColor(fw.relevance_score)}`}>
        {Math.round(fw.relevance_score * 100)}% relevance
      </span>
      <span className="text-xs text-neutral-400">{fw.region}</span>
    </div>
    <p className="text-xs text-neutral-600 line-clamp-2">{fw.relevance_reason}</p>
  </div>
);

export const StepFrameworks: React.FC = () => {
  const { profile, selectedFrameworks, toggleFramework, sessionId, setPhase } = useWizardStore();
  const frameworks = profile?.recommended_frameworks ?? [];

  const handleConfirm = async () => {
    if (selectedFrameworks.length === 0) return;
    if (sessionId) {
      try { await historyApi.updateFrameworks(sessionId, selectedFrameworks); } catch { /* non-fatal */ }
    }
    setPhase('doc_types');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-neutral-900">Select Compliance Frameworks</h2>
        <p className="text-sm text-neutral-500 mt-1">
          Pre-selected based on AI analysis (≥70% relevance). Click to toggle.
        </p>
        {profile?.analysis_summary && (
          <div className="mt-3 p-4 rounded-xl bg-primary-50 border border-primary-200">
            <p className="text-sm text-primary-800 font-medium">{profile.org_type}</p>
            <p className="text-sm text-primary-700 mt-1">{profile.analysis_summary}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {frameworks.map((fw) => (
          <FrameworkCard
            key={fw.id}
            fw={fw}
            selected={selectedFrameworks.includes(fw.id)}
            onToggle={() => toggleFramework(fw.id)}
          />
        ))}
      </div>

      <div className="flex items-center justify-between pt-2">
        <span className="text-sm text-neutral-500">{selectedFrameworks.length} framework{selectedFrameworks.length !== 1 ? 's' : ''} selected</span>
        <Button
          variant="primary"
          size="lg"
          disabled={selectedFrameworks.length === 0}
          onClick={handleConfirm}
        >
          Confirm Frameworks →
        </Button>
      </div>
    </div>
  );
};
