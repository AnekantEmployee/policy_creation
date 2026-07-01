'use client';

import React, { useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { ChatOrgInfo }    from './chat/ChatOrgInfo';
import { ChatAnalyzing }  from './chat/ChatAnalyzing';
import { ChatFrameworks } from './chat/ChatFrameworks';
import { ChatDocTypes }   from './chat/ChatDocTypes';
import { ChatGenerating } from './chat/ChatGenerating';
import { StepConversationPersonalize } from './steps/StepConversationPersonalize';
import { StepResults }    from './steps/StepResults';
import { ProgressBar }    from './ProgressBar';
import { ChevronLeft } from 'lucide-react';

export const WizardShell: React.FC = () => {
  const phase = useWizardStore((s) => s.phase);
  const setPhase = useWizardStore((s) => s.setPhase);
  const reset = useWizardStore((s) => s.reset);
  const questionIndex = useWizardStore((s) => s.questionIndex);
  const router = useRouter();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Delay scroll to ensure DOM has updated
    const timer = setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }, 100);
    return () => clearTimeout(timer);
  }, [phase, questionIndex]);

  const isChat = phase !== 'done';

  // Handle back navigation through phases
  const handleBack = () => {
    const phases = ['org_info', 'analyzing', 'frameworks', 'doc_types', 'conv_personalize', 'generating'];
    const currentIdx = phases.indexOf(phase);
    if (currentIdx > 0) {
      setPhase(phases[currentIdx - 1] as any);
    }
  };

  // Spark icon → go to landing page (no reset — preserve data)
  const handleLogoClick = () => {
    router.push('/');
  };

  // Handle exit to landing page (full reset)
  const handleExitToLanding = () => {
    reset();
    router.push('/');
  };

  const canGoBack = !['org_info', 'done'].includes(phase);

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-xl border-b border-neutral-200">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {canGoBack && (
              <button
                onClick={handleBack}
                className="p-2.5 hover:bg-neutral-100 rounded-lg transition-colors"
                title="Go back to previous step"
              >
                <ChevronLeft className="h-5 w-5 text-neutral-600" />
              </button>
            )}
            {/* Spark icon — always navigates to landing page */}
            <button
              onClick={handleLogoClick}
              className="h-8 w-8 rounded-xl bg-gradient-to-br from-primary-600 to-secondary-500 flex items-center justify-center text-white font-bold shadow-md text-base hover:opacity-80 transition-opacity"
              title="Go to home"
            >
              ⚡
            </button>
            <div>
              <h1 className="text-sm font-bold text-neutral-900 leading-tight">ComplianceIQ</h1>
              <p className="text-xs text-neutral-500 hidden sm:block">AI-powered policy generation</p>
            </div>
          </div>
          <BackendStatus />
        </div>
      </header>

      {/* Progress bar for chat phases */}
      {isChat && phase !== 'org_info' && (
        <div className="bg-white border-b border-neutral-100">
          <div className="max-w-3xl mx-auto px-4 py-2">
            <ProgressBar />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-y-auto">
        {phase === 'done' ? (
          <div className="max-w-3xl mx-auto px-4 py-8">
            <StepResults />
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-0">
            <ChatThread phase={phase} />
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>
    </div>
  );
};

const ChatThread: React.FC<{ phase: string }> = ({ phase }) => {
  const phases = ['org_info', 'analyzing', 'frameworks', 'doc_types', 'conv_personalize', 'generating'];
  const currentIdx = phases.indexOf(phase);

  return (
    <div className="space-y-6">
      {/* Always show org info step — it's the entry point */}
      <ChatOrgInfo active={phase === 'org_info'} done={currentIdx > 0} />

      {currentIdx >= 1 && <ChatAnalyzing active={phase === 'analyzing'} done={currentIdx > 1} />}
      {currentIdx >= 2 && <ChatFrameworks active={phase === 'frameworks'} done={currentIdx > 2} />}
      {currentIdx >= 3 && <ChatDocTypes active={phase === 'doc_types'} done={currentIdx > 3} />}
      {currentIdx >= 4 && <StepConversationPersonalize active={phase === 'conv_personalize'} done={currentIdx > 4} />}
      {currentIdx >= 5 && <ChatGenerating active={phase === 'generating'} done={false} />}
    </div>
  );
};

const BackendStatus: React.FC = () => {
  const [status, setStatus] = React.useState<'checking' | 'online' | 'offline'>('checking');
  React.useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? 'http://10.4.32.170:8001'}/health`, { signal: AbortSignal.timeout(3000) })
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'));
  }, []);
  return (
    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
      status === 'online'  ? 'bg-green-100 text-green-700' :
      status === 'offline' ? 'bg-red-100 text-red-700' :
                             'bg-neutral-100 text-neutral-500'}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${
        status === 'online'  ? 'bg-green-500' :
        status === 'offline' ? 'bg-red-500' :
                               'bg-neutral-400 animate-pulse'}`} />
      {status === 'checking' ? 'Checking…' : status === 'online' ? 'Online' : 'Offline'}
    </div>
  );
};
