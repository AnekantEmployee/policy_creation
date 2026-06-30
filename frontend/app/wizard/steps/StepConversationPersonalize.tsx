'use client';

/**
 * StepConversationPersonalize
 *
 * Three-phase conversational personalization:
 *   Phase A — Initial burst: extract as much as possible from user's first free-form message
 *   Phase B — Targeted questions: AI prompts for still-missing required fields (one at a time)
 *   Phase C — Open-ended: "Anything else?" prompt bar with live Google/Copilot-style suggestions
 *             until user clicks "Generate Documents"
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { personalizationApi } from '@/api/personalization';
import { BotBubble, UserBubble, ChatGroup } from '../chat/ChatBubble';
import { ChatNavigation } from '../chat/ChatNavigation';
import { Send, Zap, ChevronRight } from 'lucide-react';
import toast from 'react-hot-toast';

// ─── Types ────────────────────────────────────────────────────────────────────

interface ConvMessage {
  role: 'user' | 'assistant';
  content: string;
}

type Phase = 'initial' | 'targeted' | 'open';

// ─── Live Suggestion Bar ──────────────────────────────────────────────────────

interface SuggestionBarProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  suggestions: string[];
  placeholder: string;
  disabled?: boolean;
  submitLabel?: string;
}

const SuggestionBar: React.FC<SuggestionBarProps> = ({
  value, onChange, onSubmit, suggestions, placeholder, disabled, submitLabel = 'Send',
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeSuggIdx, setActiveSuggIdx] = useState(-1);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Filter suggestions to those matching the current input (case-insensitive)
  const filtered = value.trim().length > 0
    ? suggestions.filter(s => s.toLowerCase().includes(value.toLowerCase())).slice(0, 5)
    : suggestions.slice(0, 5);

  const shouldShow = showDropdown && filtered.length > 0;

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (shouldShow) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setActiveSuggIdx(i => Math.min(i + 1, filtered.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setActiveSuggIdx(i => Math.max(i - 1, -1)); return; }
      if (e.key === 'Tab' || (e.key === 'Enter' && activeSuggIdx >= 0)) {
        e.preventDefault();
        onChange(filtered[activeSuggIdx]);
        setShowDropdown(false);
        setActiveSuggIdx(-1);
        return;
      }
      if (e.key === 'Escape') { setShowDropdown(false); return; }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim()) onSubmit();
    }
  };

  const pickSuggestion = (s: string) => {
    onChange(s);
    setShowDropdown(false);
    setActiveSuggIdx(-1);
    setTimeout(() => inputRef.current?.focus(), 0);
  };

  return (
    <div className="relative">
      <div className={`flex items-end gap-2 bg-white border-2 rounded-2xl p-2 shadow-sm transition-colors ${disabled ? 'border-neutral-100' : 'border-neutral-200 focus-within:border-primary-400'}`}>
        <textarea
          ref={inputRef}
          rows={1}
          value={value}
          onChange={e => { onChange(e.target.value); setShowDropdown(true); setActiveSuggIdx(-1); }}
          onFocus={() => setShowDropdown(true)}
          onBlur={() => setTimeout(() => setShowDropdown(false), 150)}
          onKeyDown={handleKey}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 resize-none text-sm bg-transparent focus:outline-none text-neutral-900 placeholder-neutral-400 min-h-[36px] max-h-32 py-1.5 px-1 leading-snug overflow-y-auto"
          style={{ scrollbarWidth: 'none' }}
        />
        <button
          type="button"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
          className="shrink-0 flex items-center gap-1.5 px-3 py-2 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-xs font-semibold rounded-xl hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
        >
          <Send className="h-3.5 w-3.5" />
          {submitLabel}
        </button>
      </div>

      {/* Live suggestions dropdown */}
      {shouldShow && (
        <div
          ref={dropdownRef}
          className="absolute left-0 right-0 bottom-full mb-1.5 bg-white border border-neutral-200 rounded-xl shadow-lg z-20 overflow-hidden"
        >
          {filtered.map((s, i) => (
            <button
              key={i}
              type="button"
              onMouseDown={() => pickSuggestion(s)}
              className={`w-full text-left px-4 py-2.5 text-sm flex items-center gap-2 transition-colors ${
                i === activeSuggIdx ? 'bg-primary-50 text-primary-800' : 'text-neutral-700 hover:bg-neutral-50'
              }`}
            >
              <ChevronRight className="h-3.5 w-3.5 text-neutral-300 shrink-0" />
              <span className="truncate">{s}</span>
            </button>
          ))}
          <div className="px-4 py-1.5 border-t border-neutral-100 bg-neutral-50">
            <span className="text-xs text-neutral-400">↑↓ navigate · Tab/Enter to select · Esc to close</span>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Static suggestion pools per phase ───────────────────────────────────────

const INITIAL_PROMPTS = [
  'Our CISO is Jane Smith, ciso@company.com. We use Okta for IAM and Splunk for SIEM.',
  'We have 200 employees in India. Our DPO is John Doe, dpo@company.com.',
  'We classify data as Public, Internal, Confidential. Retention is 3 years for customer data.',
  'Our incident response email is security@company.com. We use JIRA for ticketing.',
  'We are a healthcare SaaS — 500 employees, using Azure AD and AWS Backup.',
  'We use ServiceNow for incidents and Microsoft Sentinel for log monitoring.',
  'Our data retention policy: 3 years general, 7 years financial records.',
  'Incident response SLA is 72 hours. We use Veeam for backup.',
];

const OPEN_ENDED_SUGGESTIONS = [
  'We also use Datadog for monitoring',
  'Our backup is tested quarterly',
  'We have a dedicated security team of 5',
  'All vendors sign NDAs and DPAs before access',
  'We conduct annual security awareness training',
  'Our cloud infrastructure is hosted on AWS (Mumbai region)',
  'We encrypt all data at rest using AES-256',
  'Our legal entity is registered in India',
  'We have an external audit scheduled for Q3',
  'Our CEO / executive sponsor for compliance is John Smith',
  'We use MFA for all employee accounts',
  'We hold SOC 2 Type I certification',
  'Customer data is never shared with third parties without consent',
  'Our change management board meets bi-weekly',
  'We maintain a vendor risk register updated quarterly',
];

function getFrameworkSuggestions(frameworks: string[]): string[] {
  const map: Record<string, string[]> = {
    GDPR:     ['Our ICO registration number is ZA123456', 'We have appointed a DPO — dpo@company.com', 'We process EU citizen data under legitimate interest'],
    DPDP:     ["We are registered under India's DPDP Act 2023", 'Our data fiduciary contact is privacy@company.com', 'We have appointed a Data Protection Officer'],
    HIPAA:    ['We are a covered entity — Healthcare Provider', 'All BAAs are in place with cloud vendors', 'PHI is encrypted at rest and in transit'],
    'PCI-DSS':['We are a Level 2 Merchant processing 1–6M transactions/year', 'We use tokenization for all payment data', 'Last QSA audit was completed in Q1'],
    ISO27001: ['Our ISMS scope covers all production systems', 'We conduct internal audits semi-annually', 'Asset inventory is reviewed quarterly'],
    NIST_CSF: ['We follow NIST CSF Tier 3 — Repeatable', 'Risk assessments are conducted annually', 'We have a formal vulnerability management program'],
  };
  const out: string[] = [];
  frameworks.forEach(fw => { if (map[fw]) out.push(...map[fw]); });
  return out;
}

// ─── Extracted info pill display ──────────────────────────────────────────────

const CAT_ICONS: Record<string, string> = {
  ciso_contact: '👤', dpo_contact: '👤', incident_email: '📧', legal_contact: '⚖️',
  siem_tool: '🔧', ticketing_tool: '🎫', iam_tool: '🔐', backup_tool: '💾',
  data_classification: '🏷️', retention_period: '📅', incident_response_sla: '⏱️',
  employee_count: '👥', dpa_registration: '📋', covered_entity_type: '🏥', merchant_level: '💳',
};

const FIELD_LABELS: Record<string, string> = {
  ciso_contact: 'CISO', dpo_contact: 'DPO', incident_email: 'Incident Email', legal_contact: 'Legal',
  siem_tool: 'SIEM', ticketing_tool: 'Ticketing', iam_tool: 'IAM', backup_tool: 'Backup',
  data_classification: 'Data Classification', retention_period: 'Retention', incident_response_sla: 'IR SLA',
  employee_count: 'Employees', dpa_registration: 'DPA Reg.', covered_entity_type: 'HIPAA Type', merchant_level: 'PCI Level',
};

const ExtractedPills: React.FC<{ info: Record<string, string> }> = ({ info }) => {
  const entries = Object.entries(info);
  if (entries.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {entries.map(([k, v]) => (
        <span key={k} className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-50 text-green-800 border border-green-200 rounded-full text-xs font-medium">
          <span>{CAT_ICONS[k] ?? '✓'}</span>
          <span className="text-green-600 font-normal">{FIELD_LABELS[k] ?? k}:</span>
          <span className="truncate max-w-[120px]" title={v}>{v}</span>
        </span>
      ))}
    </div>
  );
};

// ─── Main Component ───────────────────────────────────────────────────────────

interface Props { active: boolean; done: boolean; }

export const StepConversationPersonalize: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const {
    selectedGenFrameworks, selectedPolicyTypes, selectedProcedureTypes,
    orgName, orgDescription, orgCountry, sessionId,
    convPersonalizeAnswers,
    setConvPersonalizeAnswers, setConvPersonalizeHistory, mergeConvPersonalizeAnswers,
    setPhase, reset,
  } = useWizardStore();

  // ── local state ──
  const [phase, setLocalPhase] = useState<Phase>('initial');
  const [messages, setMessages] = useState<ConvMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>(INITIAL_PROMPTS);
  const [missingFields, setMissingFields] = useState<Array<{ key: string; description: string; prompt: string }>>([]);
  const [targetedIdx, setTargetedIdx] = useState(0);
  const [accumulatedInfo, setAccumulatedInfo] = useState<Record<string, string>>(convPersonalizeAnswers);
  const bottomRef = useRef<HTMLDivElement>(null);

  // scroll to bottom when messages change
  useEffect(() => {
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }), 80);
  }, [messages, loading]);

  // seed opening bot message once when active
  useEffect(() => {
    if (!active || messages.length > 0) return;
    setMessages([{
      role: 'assistant',
      content: `Hi! To personalise your ${selectedGenFrameworks.join(', ')} compliance documents, tell me about your organisation in your own words — contacts, tools, policies, anything relevant. The more you share upfront, the fewer follow-up questions I'll need to ask.`,
    }]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  // ── helpers ──
  const addMessage = (msg: ConvMessage) => setMessages(prev => [...prev, msg]);

  const buildSuggestions = useCallback((serverSuggestions: string[], info: Record<string, string>) => {
    const fwSpecific = getFrameworkSuggestions(selectedGenFrameworks);
    const open = OPEN_ENDED_SUGGESTIONS.filter(s =>
      !Object.values(info).some(v => v.toLowerCase().includes(s.toLowerCase().slice(0, 20)))
    );
    const all = [...new Set([...serverSuggestions, ...fwSpecific, ...open])];
    setSuggestions(all.slice(0, 12));
  }, [selectedGenFrameworks]);

  // ── Phase A: initial burst send ──
  const handleInitialSend = async () => {
    if (!inputValue.trim() || loading) return;
    const userMsg = inputValue.trim();
    setInputValue('');
    addMessage({ role: 'user', content: userMsg });
    setLoading(true);

    try {
      const res = await personalizationApi.chat({
        session_id: sessionId ?? 0,
        user_message: userMsg,
        frameworks: selectedGenFrameworks,
        policy_types: selectedPolicyTypes,
        procedure_types: selectedProcedureTypes,
        conversation_history: messages,
        extracted_info: accumulatedInfo,
        org_context: { org_name: orgName, org_description: orgDescription, org_country: orgCountry },
      });

      const newInfo = { ...accumulatedInfo, ...res.accumulated_info };
      setAccumulatedInfo(newInfo);
      mergeConvPersonalizeAnswers(res.accumulated_info);

      addMessage({ role: 'assistant', content: res.assistant_message });
      buildSuggestions(res.suggestions ?? [], newInfo);

      if (res.missing_info && res.missing_info.length > 0) {
        setMissingFields(res.missing_info);
        setTargetedIdx(0);
        setLocalPhase('targeted');
        // Bot asks first targeted question
        addMessage({ role: 'assistant', content: res.missing_info[0].prompt });
      } else {
        // Nothing missing — jump straight to open phase
        setLocalPhase('open');
        addMessage({ role: 'assistant', content: "Great — I've captured all the key details! Feel free to add anything else, or click Generate to proceed." });
        setSuggestions([...OPEN_ENDED_SUGGESTIONS, ...getFrameworkSuggestions(selectedGenFrameworks)]);
      }
    } catch {
      toast.error('Could not process your message — please try again');
      addMessage({ role: 'assistant', content: "Sorry, I had trouble processing that. Could you try again?" });
    } finally {
      setLoading(false);
    }
  };

  // ── Phase B: targeted question answer ──
  const handleTargetedSend = async () => {
    if (!inputValue.trim() || loading) return;
    const userMsg = inputValue.trim();
    setInputValue('');
    addMessage({ role: 'user', content: userMsg });
    setLoading(true);

    try {
      const res = await personalizationApi.chat({
        session_id: sessionId ?? 0,
        user_message: userMsg,
        frameworks: selectedGenFrameworks,
        policy_types: selectedPolicyTypes,
        procedure_types: selectedProcedureTypes,
        conversation_history: messages,
        extracted_info: accumulatedInfo,
        org_context: { org_name: orgName, org_description: orgDescription, org_country: orgCountry },
      });

      const newInfo = { ...accumulatedInfo, ...res.accumulated_info };
      setAccumulatedInfo(newInfo);
      mergeConvPersonalizeAnswers(res.accumulated_info);
      buildSuggestions(res.suggestions ?? [], newInfo);

      const nextIdx = targetedIdx + 1;
      if (nextIdx < missingFields.length) {
        setTargetedIdx(nextIdx);
        addMessage({ role: 'assistant', content: missingFields[nextIdx].prompt });
      } else {
        // All targeted questions done — move to open phase
        setLocalPhase('open');
        addMessage({ role: 'assistant', content: "Perfect — I have everything I need! Anything else you'd like to add, or click Generate Documents to proceed." });
        setSuggestions([...OPEN_ENDED_SUGGESTIONS, ...getFrameworkSuggestions(selectedGenFrameworks)]);
      }
    } catch {
      toast.error('Could not process your message — please try again');
    } finally {
      setLoading(false);
    }
  };

  // ── Phase C: open-ended additional info ──
  const handleOpenSend = async () => {
    if (!inputValue.trim() || loading) return;
    const userMsg = inputValue.trim();
    setInputValue('');
    addMessage({ role: 'user', content: userMsg });
    setLoading(true);

    try {
      const res = await personalizationApi.chat({
        session_id: sessionId ?? 0,
        user_message: userMsg,
        frameworks: selectedGenFrameworks,
        policy_types: selectedPolicyTypes,
        procedure_types: selectedProcedureTypes,
        conversation_history: messages,
        extracted_info: accumulatedInfo,
        org_context: { org_name: orgName, org_description: orgDescription, org_country: orgCountry },
      });

      const newInfo = { ...accumulatedInfo, ...res.accumulated_info };
      setAccumulatedInfo(newInfo);
      mergeConvPersonalizeAnswers(res.accumulated_info);
      buildSuggestions(res.suggestions ?? [], newInfo);

      addMessage({ role: 'assistant', content: "Got it! Anything else you'd like to include, or click Generate Documents when ready." });
    } catch {
      addMessage({ role: 'assistant', content: "Noted! Feel free to add more, or proceed to generate." });
    } finally {
      setLoading(false);
    }
  };

  // Route submit to the right phase handler
  const handleSend = () => {
    if (phase === 'initial')  return handleInitialSend();
    if (phase === 'targeted') return handleTargetedSend();
    if (phase === 'open')     return handleOpenSend();
  };

  // Skip current targeted question
  const handleSkipTargeted = () => {
    const nextIdx = targetedIdx + 1;
    if (nextIdx < missingFields.length) {
      setTargetedIdx(nextIdx);
      addMessage({ role: 'assistant', content: missingFields[nextIdx].prompt });
    } else {
      setLocalPhase('open');
      addMessage({ role: 'assistant', content: "No problem! Anything else you'd like to add, or click Generate Documents." });
      setSuggestions([...OPEN_ENDED_SUGGESTIONS, ...getFrameworkSuggestions(selectedGenFrameworks)]);
    }
  };

  // Persist history + proceed to generation
  const handleGenerate = () => {
    setConvPersonalizeHistory(messages);
    setConvPersonalizeAnswers(accumulatedInfo);
    setPhase('generating');
  };

  const handleBack  = () => setPhase('doc_types');
  const handleExit  = () => { reset(); router.push('/'); };

  // ── placeholder text by phase ──
  const placeholderText =
    phase === 'initial'  ? 'Tell us about your org: contacts, tools, data classification, retention policy…'
    : phase === 'targeted' ? 'Answer the question above, or press Skip…'
    : 'What else would you like to add? (optional)';

  const submitLabel = phase === 'open' ? 'Add' : 'Send';

  // ── DONE summary (phase already advanced past conv_personalize) ──
  if (done) {
    const count = Object.keys(accumulatedInfo).length || Object.keys(convPersonalizeAnswers).length;
    return (
      <ChatGroup>
        <BotBubble done>
          <span>{count} personalisation detail{count !== 1 ? 's' : ''} captured — documents will be tailored to your organisation.</span>
        </BotBubble>
      </ChatGroup>
    );
  }

  if (!active) return null;

  // Progress label shown below the phase strip
  const progressLabel =
    phase === 'initial'  ? 'Step 1 of 3 — Initial details'
    : phase === 'targeted' ? `Step 2 of 3 — Targeted questions (${targetedIdx + 1} / ${missingFields.length})`
    : 'Step 3 of 3 — Anything else?';

  return (
    <div className="space-y-4">
      {/* Phase progress strip */}
      <div className="space-y-1">
        <div className="flex items-center gap-3 px-1">
        {(['initial', 'targeted', 'open'] as Phase[]).map((p, i) => (
          <React.Fragment key={p}>
            <div className={`flex items-center gap-1.5 text-xs font-medium ${phase === p ? 'text-primary-600' : i < (['initial','targeted','open'] as Phase[]).indexOf(phase) ? 'text-neutral-400 line-through' : 'text-neutral-300'}`}>
              <span className={`h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold ${phase === p ? 'bg-primary-600 text-white' : i < (['initial','targeted','open'] as Phase[]).indexOf(phase) ? 'bg-neutral-300 text-white' : 'bg-neutral-100 text-neutral-400'}`}>{i + 1}</span>
              <span className="hidden sm:inline">{p === 'initial' ? 'Tell us' : p === 'targeted' ? 'Quick Qs' : 'Anything else?'}</span>
            </div>
            {i < 2 && <div className={`flex-1 h-0.5 rounded ${i < (['initial','targeted','open'] as Phase[]).indexOf(phase) ? 'bg-primary-400' : 'bg-neutral-200'}`} />}
          </React.Fragment>
        ))}
        </div>
        <p className="text-xs text-neutral-500 px-1">{progressLabel}</p>
      </div>

      {/* Extracted info pills */}
      {Object.keys(accumulatedInfo).length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-xl px-4 py-3">
          <p className="text-xs font-semibold text-green-700 mb-1">✓ Captured so far</p>
          <ExtractedPills info={accumulatedInfo} />
        </div>
      )}

      {/* Chat message thread */}
      <div className="space-y-3 min-h-[80px]">
        {messages.map((msg, i) => (
          msg.role === 'assistant'
            ? <BotBubble key={i}>{msg.content}</BotBubble>
            : <UserBubble key={i}>{msg.content}</UserBubble>
        ))}
        {loading && (
          <BotBubble>
            <div className="flex items-center gap-2">
              <div className="flex gap-1">{[0,1,2].map(i => <span key={i} className="h-2 w-2 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: `${i*0.15}s` }} />)}</div>
              <span className="text-xs text-neutral-400">Processing…</span>
            </div>
          </BotBubble>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="space-y-2">
        <SuggestionBar
          value={inputValue}
          onChange={setInputValue}
          onSubmit={handleSend}
          suggestions={suggestions}
          placeholder={placeholderText}
          disabled={loading}
          submitLabel={submitLabel}
        />

        {/* Skip button for targeted phase */}
        {phase === 'targeted' && !loading && (
          <div className="flex justify-end">
            <button type="button" onClick={handleSkipTargeted}
              className="text-xs text-neutral-400 hover:text-neutral-600 underline transition-colors">
              Skip this question →
            </button>
          </div>
        )}

        {/* Generate button — always visible in open phase, also available after initial */}
        {(phase === 'open' || phase === 'targeted') && (
          <button
            type="button"
            onClick={handleGenerate}
            className="w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 transition-opacity shadow-sm"
          >
            <Zap className="h-4 w-4" />
            Generate Documents
          </button>
        )}
      </div>

      <ChatNavigation onBack={handleBack} onExit={handleExit} canGoBack={true} />
    </div>
  );
};
