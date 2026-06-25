'use client';

import React, { useEffect, useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { historyApi } from '@/api/history';
import { frameworksApi } from '@/api/frameworks';
import { Button } from '@/app/components/Button';
import type { Framework, FrameworkMatch } from '@/types';

const scoreColor = (s: number) =>
  s >= 0.8 ? 'text-green-600' : s >= 0.6 ? 'text-amber-600' : 'text-red-500';

// Card for AI-suggested frameworks (with relevance score bar)
const AiFrameworkCard: React.FC<{ fw: FrameworkMatch; selected: boolean; onToggle: () => void }> = ({ fw, selected, onToggle }) => (
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

// Card for manually-chosen frameworks from the full catalog
const CatalogFrameworkCard: React.FC<{ fw: Framework; selected: boolean; onToggle: () => void }> = ({ fw, selected, onToggle }) => (
  <div
    className={`relative rounded-xl border-2 p-4 cursor-pointer transition-all duration-200 ${
      selected ? 'border-secondary-500 bg-secondary-50 shadow-md' : 'border-neutral-200 bg-white hover:border-secondary-300'
    }`}
    onClick={onToggle}
  >
    {selected && (
      <div className="absolute top-3 right-3 h-5 w-5 rounded-full bg-secondary-600 flex items-center justify-center text-white text-xs font-bold">✓</div>
    )}
    <div className="flex items-start gap-3 mb-2">
      <span className="text-2xl">{fw.icon}</span>
      <div className="min-w-0">
        <span className="font-bold text-neutral-900 text-sm block">{fw.id}</span>
        <p className="text-xs text-neutral-500 truncate">{fw.name}</p>
      </div>
    </div>
    <div className="flex justify-between items-center mb-2">
      <span className="text-xs text-neutral-400">{fw.region}</span>
    </div>
    <p className="text-xs text-neutral-600 line-clamp-2">{fw.description}</p>
  </div>
);

export const StepFrameworks: React.FC = () => {
  const { profile, selectedFrameworks, toggleFramework, sessionId, setPhase } = useWizardStore();
  const aiFrameworks = profile?.recommended_frameworks ?? [];
  const aiFrameworkIds = new Set(aiFrameworks.map((f) => f.id));

  const [showCatalog, setShowCatalog] = useState(false);
  const [allFrameworks, setAllFrameworks] = useState<Framework[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);

  // Frameworks from the full catalog that weren't already suggested by AI
  const extraFrameworks = allFrameworks.filter((f) => !aiFrameworkIds.has(f.id));

  const handleToggleCatalog = async () => {
    if (!showCatalog && allFrameworks.length === 0) {
      setCatalogLoading(true);
      try {
        const data = await frameworksApi.list();
        setAllFrameworks(data);
      } catch {
        // non-fatal — catalog just won't show
      } finally {
        setCatalogLoading(false);
      }
    }
    setShowCatalog((v) => !v);
  };

  const handleConfirm = async () => {
    if (selectedFrameworks.length === 0) return;
    if (sessionId) {
      try { await historyApi.updateFrameworks(sessionId, selectedFrameworks); } catch { /* non-fatal */ }
    }
    setPhase('doc_types');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-neutral-900">Select Compliance Frameworks</h2>
        <p className="text-sm text-neutral-500 mt-1">
          AI-recommended frameworks are shown below. You can also add more from the full catalog.
        </p>
        {profile?.analysis_summary && (
          <div className="mt-3 p-4 rounded-xl bg-primary-50 border border-primary-200">
            <p className="text-sm text-primary-800 font-medium">{profile.org_type}</p>
            <p className="text-sm text-primary-700 mt-1">{profile.analysis_summary}</p>
          </div>
        )}
      </div>

      {/* AI Suggestions */}
      <div>
        <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">
          🤖 AI Recommended
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {aiFrameworks.map((fw) => (
            <AiFrameworkCard
              key={fw.id}
              fw={fw}
              selected={selectedFrameworks.includes(fw.id)}
              onToggle={() => toggleFramework(fw.id)}
            />
          ))}
        </div>
      </div>

      {/* Divider + Browse More toggle */}
      <div className="border-t border-neutral-200 pt-4">
        <button
          onClick={handleToggleCatalog}
          className="flex items-center gap-2 text-sm font-semibold text-primary-600 hover:text-primary-800 transition-colors"
        >
          <span className={`transition-transform duration-200 ${showCatalog ? 'rotate-90' : ''}`}>▶</span>
          {showCatalog ? 'Hide full framework catalog' : '+ Browse all frameworks to add more'}
        </button>
      </div>

      {/* Full Catalog */}
      {showCatalog && (
        <div>
          <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-3">
            📚 All Frameworks — Choose Any Additional
          </p>
          {catalogLoading ? (
            <div className="flex items-center gap-2 text-sm text-neutral-500 py-4">
              <svg className="animate-spin h-4 w-4 text-primary-500" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Loading frameworks…
            </div>
          ) : extraFrameworks.length === 0 ? (
            <p className="text-sm text-neutral-500 py-2">All available frameworks are already listed above.</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {extraFrameworks.map((fw) => (
                <CatalogFrameworkCard
                  key={fw.id}
                  fw={fw}
                  selected={selectedFrameworks.includes(fw.id)}
                  onToggle={() => toggleFramework(fw.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-neutral-100">
        <span className="text-sm text-neutral-500">
          {selectedFrameworks.length} framework{selectedFrameworks.length !== 1 ? 's' : ''} selected
        </span>
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
