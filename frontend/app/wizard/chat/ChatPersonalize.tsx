'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { personalizationApi } from '@/api/personalization';
import { BotBubble, UserBubble, ChatGroup } from './ChatBubble';
import { ChatNavigation } from './ChatNavigation';
import { ChevronLeft } from 'lucide-react';
import type { PersonalizationQuestion } from '@/types';

const CAT_ICONS: Record<string, string> = {
  contacts: '👤', tools: '🔧', roles: '👥', processes: '⚙️', legal: '⚖️', technical: '💻',
};

function buildStaticQuestions(frameworks: string[]): PersonalizationQuestion[] {
  const base: PersonalizationQuestion[] = [
    { key: 'ciso_contact',          label: 'CISO / Security Officer — name and email',       hint: 'e.g. Jane Smith, ciso@acme.com',          type: 'text',  category: 'contacts' },
    { key: 'dpo_contact',           label: 'Data Protection Officer — name and email',        hint: 'e.g. John Doe, dpo@acme.com',             type: 'text',  category: 'contacts' },
    { key: 'incident_email',        label: 'Security incident reporting email / alias',       hint: 'e.g. security@acme.com',                  type: 'email', category: 'contacts' },
    { key: 'legal_contact',         label: 'Legal / Compliance counsel contact',              hint: 'e.g. General Counsel or external firm',   type: 'text',  category: 'contacts' },
    { key: 'siem_tool',             label: 'SIEM / log monitoring tool used',                 hint: 'e.g. Splunk, Microsoft Sentinel, Datadog', type: 'text', category: 'tools' },
    { key: 'ticketing_tool',        label: 'Incident & task ticketing system',                hint: 'e.g. JIRA, ServiceNow, Freshdesk',         type: 'text', category: 'tools' },
    { key: 'iam_tool',              label: 'Identity & Access Management (IAM) tool',         hint: 'e.g. Okta, Azure AD, Google Workspace',    type: 'text', category: 'tools' },
    { key: 'backup_tool',           label: 'Backup & recovery tool',                          hint: 'e.g. Veeam, AWS Backup, Acronis',          type: 'text', category: 'tools' },
    { key: 'data_classification',   label: 'Data classification levels your org uses',        hint: 'e.g. Public, Internal, Confidential',      type: 'text', category: 'processes' },
    { key: 'retention_period',      label: 'Standard data retention period',                  hint: 'e.g. 3 years customer data',               type: 'text', category: 'processes' },
    { key: 'incident_response_sla', label: 'Incident response SLA / notification window',     hint: 'e.g. 72 hours (GDPR), 60 days (HIPAA)',   type: 'text', category: 'processes' },
    { key: 'employee_count',        label: 'Approximate employee count',                      hint: 'e.g. 50, 200–500, 1000+',                 type: 'text', category: 'technical' },
  ];
  if (frameworks.includes('GDPR'))
    base.splice(2, 0, { key: 'dpa_registration', label: 'ICO / DPA registration number (if applicable)', hint: 'e.g. ZA123456 (UK ICO)', type: 'text', category: 'legal' });
  if (frameworks.includes('HIPAA'))
    base.splice(2, 0, { key: 'covered_entity_type', label: 'HIPAA covered entity type', hint: '', type: 'select', options: ['Healthcare Provider', 'Health Plan', 'Health Clearinghouse', 'Business Associate'], category: 'legal' });
  if (frameworks.includes('PCI-DSS'))
    base.splice(2, 0, { key: 'merchant_level', label: 'PCI-DSS merchant / service provider level', hint: 'e.g. Level 1', type: 'select', options: ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Service Provider Level 1', 'Service Provider Level 2'], category: 'legal' });
  return base;
}

interface QuestionBlockProps {
  q: PersonalizationQuestion;
  index: number;
  total: number;
  onSave: (val: string) => void;
  onSkip: () => void;
  onBack: () => void;
  canGoBack: boolean;
}

const QuestionBlock: React.FC<QuestionBlockProps> = ({ q, index, total, onSave, onSkip, onBack, canGoBack }) => {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (value.trim()) onSave(value.trim());
    else onSkip();
    // Clear input after submission
    setValue('');
  };

  return (
    <div className="ml-11">
      <div className="bg-white rounded-2xl border-2 border-primary-200 shadow-sm p-4 space-y-3 max-w-xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-primary-600">
            <span>{CAT_ICONS[q.category] ?? '📌'}</span>
            <span>{q.category}</span>
          </div>
          <span className="text-xs text-neutral-400">{index + 1} / {total}</span>
        </div>

        <p className="text-sm font-semibold text-neutral-900">{q.label}</p>

        <form onSubmit={handleSubmit} className="space-y-3">
          {q.type === 'select' && q.options ? (
            <select value={value} onChange={e => setValue(e.target.value)}
              className="w-full px-3 py-2 text-sm rounded-lg border-2 border-neutral-200 bg-white focus:outline-none focus:border-primary-500 transition-colors">
              <option value="">— Select one —</option>
              {q.options.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          ) : q.type === 'textarea' ? (
            <textarea value={value} onChange={e => setValue(e.target.value)} placeholder={q.hint} rows={3}
              className="w-full px-3 py-2 text-sm rounded-lg border-2 border-neutral-200 bg-neutral-50 focus:bg-white focus:outline-none focus:border-primary-500 transition-colors resize-none" />
          ) : (
            <input type={q.type} value={value} onChange={e => setValue(e.target.value)} placeholder={q.hint}
              onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleSubmit(e as unknown as React.FormEvent); } }}
              className="w-full px-3 py-2 text-sm rounded-lg border-2 border-neutral-200 bg-neutral-50 focus:bg-white focus:outline-none focus:border-primary-500 transition-colors" />
          )}

          <p className="text-xs text-neutral-400">💡 {q.hint}</p>

          <div className="flex gap-2">
            {canGoBack && (
              <button type="button" onClick={onBack}
                className="px-3 py-2 text-xs font-medium text-neutral-500 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors flex items-center gap-1">
                <ChevronLeft className="h-3.5 w-3.5" />
                Back
              </button>
            )}
            <button type="submit"
              className="flex-1 py-2 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-xs font-semibold rounded-lg hover:opacity-90 transition-opacity">
              Save & Next →
            </button>
            <button type="button" onClick={onSkip}
              className="px-4 py-2 text-xs font-medium text-neutral-500 border border-neutral-200 rounded-lg hover:bg-neutral-50 transition-colors">
              Skip
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

interface Props { active: boolean; done: boolean; }

export const ChatPersonalize: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const {
    selectedGenFrameworks, selectedPolicyTypes, selectedProcedureTypes,
    orgName, orgDescription, orgCountry,
    questions, answers, questionIndex,
    setQuestions, setAnswer, nextQuestion, removeCurrentAnswer, setPhase, reset,
  } = useWizardStore();

  const [loading,   setLoading]   = useState(false);
  const [aiSource,  setAiSource]  = useState(false);
  // answered Q's rendered as chat bubbles
  const [history,   setHistory]   = useState<Array<{ q: PersonalizationQuestion; answer: string | null }>>([]);

  // Load questions once when active
  useEffect(() => {
    if (!active || questions.length > 0) return;
    setLoading(true);
    personalizationApi.generateQuestions({
      org_name:        orgName,
      org_description: orgDescription,
      org_country:     orgCountry,
      frameworks:      selectedGenFrameworks,
      policy_types:    selectedPolicyTypes,
      procedure_types: selectedProcedureTypes,
    }).then(({ questions: qs, source }) => {
      setQuestions(qs);
      setAiSource(source === 'ai');
    }).catch(() => {
      // fallback: use static questions built client-side
      const staticQs = buildStaticQuestions(selectedGenFrameworks);
      setQuestions(staticQs);
      setAiSource(false);
    }).finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  // Advance to generating when all questions done
  useEffect(() => {
    if (active && questions.length > 0 && questionIndex >= questions.length) {
      setPhase('generating');
    }
  }, [active, questionIndex, questions.length, setPhase]);

  const handleSave = (val: string) => {
    const q = questions[questionIndex];
    setAnswer(q.key, val);
    setHistory(h => [...h, { q, answer: val }]);
    nextQuestion();
  };

  const handleSkip = () => {
    const q = questions[questionIndex];
    setHistory(h => [...h, { q, answer: null }]);
    nextQuestion();
  };

  const handleBack = () => {
    if (questionIndex > 0) {
      // Remove the last history item
      setHistory(h => h.slice(0, -1));
      // Remove the answer and go back
      removeCurrentAnswer();
    }
  };

  const handleExit = () => {
    reset();
    router.push('/');
  };

  // DONE summary
  if (done) {
    const count = Object.keys(answers).length;
    return (
      <ChatGroup>
        <BotBubble done>
          <span>{count} personalization detail{count !== 1 ? 's' : ''} captured. Documents will use your real contacts and tools.</span>
        </BotBubble>
        {active && (
          <ChatNavigation
            onBack={() => setPhase('doc_types')}
            onExit={handleExit}
            canGoBack={true}
          />
        )}
      </ChatGroup>
    );
  }

  if (!active) return null;

  const current = questions[questionIndex];
  const total   = questions.length;
  const pct     = total > 0 ? Math.round((questionIndex / total) * 100) : 0;

  return (
    <div className="space-y-3">
      {/* Intro bot message */}
      <BotBubble>
        {loading ? (
          <div className="flex items-center gap-3">
            <div className="flex gap-1">
              {[0,1,2].map(i => <span key={i} className="h-2 w-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}
            </div>
            <span>{aiSource === false ? 'Generating personalized questions…' : 'Preparing questions…'}</span>
          </div>
        ) : (
          <div className="space-y-1">
            <p>I have <strong>{total} targeted questions</strong> for you.{aiSource ? ' 🤖 Tailored by AI to your specific setup.' : ''}</p>
            <p className="text-neutral-500 text-xs">Answer what you can — skip anything that doesn't apply. The more you fill in, the more personalized your documents will be.</p>
          </div>
        )}
      </BotBubble>

      {/* Answered questions as chat bubbles */}
      {history.map(({ q, answer }, i) => (
        <div key={i} className="space-y-1">
          <div className="ml-11">
            <p className="text-xs text-neutral-400 mb-1">{CAT_ICONS[q.category]} {q.label}</p>
          </div>
          <UserBubble>
            {answer ?? <span className="italic opacity-70">skipped</span>}
          </UserBubble>
        </div>
      ))}

      {/* Progress indicator */}
      {!loading && total > 0 && questionIndex < total && (
        <div className="ml-11 max-w-xl">
          <div className="flex justify-between text-xs text-neutral-400 mb-1">
            <span>Question {questionIndex + 1} of {total}</span>
            <span>{Object.keys(answers).length} answered</span>
          </div>
          <div className="h-1.5 bg-neutral-200 rounded-full overflow-hidden">
            <div className="h-1.5 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
          </div>
        </div>
      )}

      {/* Current question block */}
      {!loading && current && (
        <>
          <QuestionBlock q={current} index={questionIndex} total={total} onSave={handleSave} onSkip={handleSkip} onBack={handleBack} canGoBack={questionIndex > 0} />
          <ChatNavigation
            onBack={questionIndex > 0 ? handleBack : () => setPhase('doc_types')}
            onExit={handleExit}
            backLabel={questionIndex > 0 ? 'Previous' : 'Back'}
            canGoBack={true}
          />
        </>
      )}

      {/* Skip all */}
      {!loading && current && (
        <div className="ml-11 text-center">
          <button type="button" onClick={() => setPhase('generating')}
            className="text-xs text-neutral-400 hover:text-neutral-600 underline">
            Skip all remaining questions and generate now
          </button>
        </div>
      )}
    </div>
  );
};
