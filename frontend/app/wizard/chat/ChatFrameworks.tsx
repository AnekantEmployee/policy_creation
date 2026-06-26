'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { frameworksApi } from '@/api/frameworks';
import { BotBubble, UserBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';
import { historyApi } from '@/api/history';
import type { Framework } from '@/types';

interface Props { active: boolean; done: boolean; }

function scoreColor(score: number) {
  if (score >= 0.8) return '#22c55e';
  if (score >= 0.6) return '#eab308';
  return '#ef4444';
}

export const ChatFrameworks: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const { profile, selectedFrameworks, toggleFramework, sessionId, setPhase, reset } = useWizardStore();
  const aiFrameworks = profile?.recommended_frameworks ?? [];
  const aiFrameworkIds = new Set(aiFrameworks.map((f) => f.id));

  const [showCatalog, setShowCatalog] = useState(false);
  const [allFrameworks, setAllFrameworks] = useState<Framework[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);

  const extraFrameworks = allFrameworks.filter((f) => !aiFrameworkIds.has(f.id));

  const handleToggleCatalog = async () => {
    if (!showCatalog && allFrameworks.length === 0) {
      setCatalogLoading(true);
      try {
        const data = await frameworksApi.list();
        setAllFrameworks(data);
      } catch {
        // non-fatal
      } finally {
        setCatalogLoading(false);
      }
    }
    setShowCatalog((v) => !v);
  };

  const handleConfirm = async () => {
    if (sessionId) {
      try { await historyApi.updateFrameworks(sessionId, selectedFrameworks); } catch {}
    }
    setPhase('doc_types');
  };

  const handleBack = () => setPhase('analyzing');
  const handleExit = () => {
    reset();
    router.push('/');
  };

  if (done) {
    return (
      <ChatGroup>
        <BotBubble done>Frameworks confirmed.</BotBubble>
        <UserBubble>
          <span>{selectedFrameworks.join(', ')}</span>
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

  const summary = profile?.analysis_summary;
  const industries = profile?.industries_detected.join(', ');
  const orgType = profile?.org_type;

  return (
    <ChatGroup>
      <BotBubble>
        <div className="space-y-2">
          <p><span className="font-semibold text-green-700">✅ Analysis complete!</span> Organization type: <span className="font-semibold">{orgType}</span>.</p>
          {summary && <p className="text-neutral-600 text-xs italic">{summary}</p>}
          {industries && <p className="text-xs text-neutral-500">🏭 Industries: {industries}</p>}
          <p className="mt-1">Choose the compliance frameworks your organization needs. Our recommendations are based on your industry and location.</p>
        </div>
      </BotBubble>

      <div className="ml-11 space-y-3">

        {/* AI Suggested */}
        <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">🤖 AI Recommended</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {aiFrameworks.map(fw => {
            const selected = selectedFrameworks.includes(fw.id);
            const pct = Math.round(fw.relevance_score * 100);
            return (
              <button key={fw.id} onClick={() => toggleFramework(fw.id)}
                className={`text-left p-3 rounded-xl border-2 transition-all duration-200 ${selected ? 'border-primary-500 bg-primary-50' : 'border-neutral-200 bg-white hover:border-neutral-300'}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{fw.icon}</span>
                    <span className="text-sm font-bold text-neutral-900">{fw.id}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {fw.is_mandatory && <span className="text-xs px-1.5 py-0.5 bg-red-100 text-red-700 rounded-full">Mandatory</span>}
                    {selected && <span className="text-xs px-1.5 py-0.5 bg-primary-100 text-primary-700 rounded-full">✓ Selected</span>}
                  </div>
                </div>
                <div className="h-1.5 bg-neutral-200 rounded-full mb-1">
                  <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, background: scoreColor(fw.relevance_score) }} />
                </div>
                <p className="text-xs font-medium" style={{ color: scoreColor(fw.relevance_score) }}>{pct}% relevance</p>
                <p className="text-xs text-neutral-500 mt-1 line-clamp-2">{fw.relevance_reason}</p>
              </button>
            );
          })}
        </div>

        {/* Browse More toggle */}
        <div className="border-t border-neutral-200 pt-2">
          <button
            onClick={handleToggleCatalog}
            className="flex items-center gap-2 text-sm font-semibold text-primary-600 hover:text-primary-800 transition-colors"
          >
            <span className={`transition-transform duration-200 inline-block ${showCatalog ? 'rotate-90' : ''}`}>▶</span>
            {showCatalog ? 'Hide full catalog' : '+ Add more frameworks'}
          </button>
        </div>

        {/* Full Catalog */}
        {showCatalog && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">📚 All Frameworks</p>
            {catalogLoading ? (
              <div className="flex items-center gap-2 text-sm text-neutral-500 py-2">
                <svg className="animate-spin h-4 w-4 text-primary-500" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                </svg>
                Loading…
              </div>
            ) : extraFrameworks.length === 0 ? (
              <p className="text-xs text-neutral-500">All available frameworks are already listed above.</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {extraFrameworks.map(fw => {
                  const selected = selectedFrameworks.includes(fw.id);
                  return (
                    <button key={fw.id} onClick={() => toggleFramework(fw.id)}
                      className={`text-left p-3 rounded-xl border-2 transition-all duration-200 ${selected ? 'border-secondary-500 bg-secondary-50' : 'border-neutral-200 bg-white hover:border-neutral-300'}`}>
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{fw.icon}</span>
                          <span className="text-sm font-bold text-neutral-900">{fw.id}</span>
                        </div>
                        {selected && <span className="text-xs px-1.5 py-0.5 bg-secondary-100 text-secondary-700 rounded-full">✓ Added</span>}
                      </div>
                      <p className="text-xs text-neutral-400 mb-1">{fw.region}</p>
                      <p className="text-xs text-neutral-500 line-clamp-2">{fw.description}</p>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Confirm */}
        <div className="space-y-2 pt-1">
          <button
            disabled={selectedFrameworks.length === 0}
            onClick={handleConfirm}
            className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity shadow-sm">
            Confirm {selectedFrameworks.length} Framework{selectedFrameworks.length !== 1 ? 's' : ''} →
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
