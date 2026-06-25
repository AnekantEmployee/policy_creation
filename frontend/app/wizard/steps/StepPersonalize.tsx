'use client';

import React, { useEffect, useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { Button } from '@/app/components/Button';
import type { PersonalizationQuestion } from '@/types';

// Static fallback questions — mirrors chatbot.py static list
function buildStaticQuestions(frameworks: string[]): PersonalizationQuestion[] {
  const base: PersonalizationQuestion[] = [
    { key: 'ciso_contact', label: 'CISO / Security Officer — name and email', hint: 'e.g. Jane Smith, ciso@acme.com', type: 'text', category: 'contacts' },
    { key: 'dpo_contact', label: 'Data Protection Officer — name and email', hint: 'e.g. John Doe, dpo@acme.com', type: 'text', category: 'contacts' },
    { key: 'incident_email', label: 'Security incident reporting email / alias', hint: 'e.g. security@acme.com', type: 'email', category: 'contacts' },
    { key: 'legal_contact', label: 'Legal / Compliance counsel contact', hint: 'e.g. General Counsel or external firm name + email', type: 'text', category: 'contacts' },
    { key: 'siem_tool', label: 'SIEM / log monitoring tool used', hint: 'e.g. Splunk, Microsoft Sentinel, Datadog', type: 'text', category: 'tools' },
    { key: 'ticketing_tool', label: 'Incident & task ticketing system', hint: 'e.g. JIRA, ServiceNow, Freshdesk', type: 'text', category: 'tools' },
    { key: 'iam_tool', label: 'Identity & Access Management (IAM) tool', hint: 'e.g. Okta, Azure AD, Google Workspace', type: 'text', category: 'tools' },
    { key: 'backup_tool', label: 'Backup & recovery tool', hint: 'e.g. Veeam, AWS Backup, Acronis', type: 'text', category: 'tools' },
    { key: 'data_classification', label: 'Data classification levels your org uses', hint: 'e.g. Public, Internal, Confidential, Restricted', type: 'text', category: 'processes' },
    { key: 'retention_period', label: 'Standard data retention period', hint: 'e.g. 3 years customer data, 7 years financial records', type: 'text', category: 'processes' },
    { key: 'incident_response_sla', label: 'Incident response SLA / notification window', hint: 'e.g. 72 hours for breach notification (GDPR)', type: 'text', category: 'processes' },
    { key: 'employee_count', label: 'Approximate employee count', hint: 'e.g. 50, 200–500, 1000+', type: 'text', category: 'technical' },
  ];
  if (frameworks.includes('GDPR')) {
    base.splice(2, 0, { key: 'dpa_registration', label: 'ICO / DPA registration number (if applicable)', hint: 'e.g. ZA123456 (UK ICO)', type: 'text', category: 'legal' });
  }
  if (frameworks.includes('HIPAA')) {
    base.splice(2, 0, { key: 'covered_entity_type', label: 'HIPAA covered entity type', hint: '', type: 'select', options: ['Healthcare Provider', 'Health Plan', 'Health Clearinghouse', 'Business Associate'], category: 'legal' });
  }
  return base;
}

const CAT_ICONS: Record<string, string> = { contacts: '👤', tools: '🔧', roles: '👥', processes: '⚙️', legal: '⚖️', technical: '💻' };

export const StepPersonalize: React.FC = () => {
  const { selectedGenFrameworks, selectedPolicyTypes, selectedProcedureTypes, orgName, orgDescription, orgCountry,
          questions, questionIndex, answers, setQuestions, setAnswer, nextQuestion, setPhase } = useWizardStore();

  const [value, setValue] = useState('');

  useEffect(() => {
    if (questions.length === 0) {
      setQuestions(buildStaticQuestions(selectedGenFrameworks));
    }
  }, [questions.length, selectedGenFrameworks, setQuestions]);

  const q = questions[questionIndex];
  const total = questions.length;
  const answered = Object.keys(answers).length;

  const handleSave = () => {
    if (value.trim()) setAnswer(q.key, value.trim());
    setValue('');
    nextQuestion();
  };

  const handleSkip = () => {
    setValue('');
    nextQuestion();
  };

  useEffect(() => {
    if (questions.length > 0 && questionIndex >= questions.length) {
      setPhase('generating');
    }
  }, [questionIndex, questions.length, setPhase]);

  if (!q) return null;

  const progress = Math.round((questionIndex / total) * 100);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-neutral-900">Personalization Details</h2>
        <p className="text-sm text-neutral-500 mt-1">
          Answer these questions so your documents use real contacts and tools instead of generic placeholders.
        </p>
      </div>

      {/* Progress */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs text-neutral-500">
          <span>Question {questionIndex + 1} of {total}</span>
          <span>{answered} answered</span>
        </div>
        <div className="h-2 bg-neutral-200 rounded-full overflow-hidden">
          <div className="h-2 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Question card */}
      <div className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-primary-600">
          <span>{CAT_ICONS[q.category] ?? '📌'}</span>
          <span>{q.category}</span>
        </div>

        <p className="text-base font-semibold text-neutral-900">{q.label}</p>

        {q.type === 'select' && q.options ? (
          <select
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className="w-full px-4 py-2.5 text-sm rounded-lg border-2 border-neutral-200 bg-white focus:outline-none focus:border-primary-500 transition-all duration-200"
          >
            <option value="">— Select one —</option>
            {q.options.map((o) => <option key={o} value={o}>{o}</option>)}
          </select>
        ) : q.type === 'textarea' ? (
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={q.hint}
            rows={3}
            className="w-full px-4 py-2.5 text-sm rounded-lg border-2 border-neutral-200 bg-white focus:outline-none focus:border-primary-500 transition-all duration-200 resize-none"
          />
        ) : (
          <input
            type={q.type}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={q.hint}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSave(); } }}
            className="w-full px-4 py-2.5 text-sm rounded-lg border-2 border-neutral-200 bg-white focus:outline-none focus:border-primary-500 focus:bg-primary-50 transition-all duration-200"
          />
        )}

        <p className="text-xs text-neutral-400">💡 {q.hint}</p>

        <div className="flex gap-3 pt-2">
          <Button variant="primary" fullWidth onClick={handleSave}>
            Save & Next →
          </Button>
          <Button variant="outline" onClick={handleSkip}>
            Skip
          </Button>
        </div>
      </div>

      {/* Skip all */}
      <div className="text-center">
        <button
          type="button"
          onClick={() => setPhase('generating')}
          className="text-xs text-neutral-400 hover:text-neutral-600 underline"
        >
          Skip all remaining questions and generate now
        </button>
      </div>
    </div>
  );
};
