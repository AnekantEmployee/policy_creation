'use client';

import React, { useState, useEffect } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { Button } from '@/app/components/Button';
import { Badge } from '@/app/components/Badge';
import { Card, CardBody, CardHeader } from '@/app/components/Card';
import { FileText, Zap, ChevronDown, ChevronRight, RefreshCw, Download, Clock, RotateCcw } from 'lucide-react';
import type { GeneratedPolicy, GeneratedProcedure, HistorySession } from '@/types';
import { downloadWizardDocx } from '@/api/export';
import { historyApi } from '@/api/history';
import toast from 'react-hot-toast';

// ── Policy card ───────────────────────────────────────────────────────────────
const PolicyCard: React.FC<{ policy: GeneratedPolicy }> = ({ policy }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-neutral-200 rounded-xl overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-4 text-left hover:bg-neutral-50 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-8 w-8 rounded-lg bg-primary-50 flex items-center justify-center shrink-0">
            <FileText className="h-4 w-4 text-primary-600" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-neutral-900 truncate">{policy.title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-neutral-400">{policy.policy_id}</span>
              <Badge variant="primary" size="sm">{policy.framework}</Badge>
              <Badge variant="info" size="sm">v{policy.version}</Badge>
            </div>
          </div>
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-neutral-400 shrink-0" />}
      </button>
      {open && (
        <div className="border-t border-neutral-200 p-4 space-y-4 animate-fade-in">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            {[['Owner', policy.owner], ['Classification', policy.classification],
              ['Effective', policy.effective_date], ['Review', policy.review_date]].map(([l, v]) => (
              <div key={l} className="bg-neutral-50 rounded-lg p-2">
                <p className="text-neutral-500 mb-0.5">{l}</p>
                <p className="font-medium text-neutral-900 truncate">{v}</p>
              </div>
            ))}
          </div>
          {policy.sections.map((sec, i) => (
            <div key={i} className="border-l-2 border-primary-300 pl-4">
              <p className="text-xs font-semibold text-primary-700 uppercase tracking-wide mb-1">{sec.title}</p>
              <p className="text-sm text-neutral-700 whitespace-pre-wrap">{sec.content}</p>
              {sec.references.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2">
                  {sec.references.map((r, j) => (
                    <span key={j} className="px-2 py-0.5 text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded">{r}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div className="pt-2">
            <button onClick={() => downloadWizardDocx(policy.title, [policy.framework], [policy], [])}
              className="flex items-center gap-2 text-xs text-primary-600 hover:text-primary-700 font-medium">
              <Download className="h-3.5 w-3.5" /> Download (.docx)
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── Procedure card ────────────────────────────────────────────────────────────
const ProcedureCard: React.FC<{ proc: GeneratedProcedure }> = ({ proc }) => {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-neutral-200 rounded-xl overflow-hidden">
      <button className="w-full flex items-center justify-between p-4 text-left hover:bg-neutral-50 transition-colors"
        onClick={() => setOpen((o) => !o)}>
        <div className="flex items-center gap-3 min-w-0">
          <div className="h-8 w-8 rounded-lg bg-secondary-50 flex items-center justify-center shrink-0">
            <Zap className="h-4 w-4 text-secondary-600" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-neutral-900 truncate">{proc.title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs text-neutral-400">{proc.procedure_id}</span>
              <Badge variant="secondary" size="sm">{proc.framework}</Badge>
              <span className="text-xs text-neutral-400">{proc.frequency}</span>
            </div>
          </div>
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-neutral-400 shrink-0" />}
      </button>
      {open && (
        <div className="border-t border-neutral-200 p-4 space-y-4 animate-fade-in">
          {proc.purpose && <div className="border-l-2 border-secondary-300 pl-4"><p className="text-xs font-semibold text-secondary-700 uppercase tracking-wide mb-1">Purpose</p><p className="text-sm text-neutral-700">{proc.purpose}</p></div>}
          {proc.scope && <div className="border-l-2 border-neutral-300 pl-4"><p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-1">Scope</p><p className="text-sm text-neutral-700">{proc.scope}</p></div>}
          <div className="space-y-3">
            {proc.steps.map((step) => (
              <div key={step.step_number} className="bg-neutral-50 rounded-lg p-3 border border-neutral-200">
                <div className="flex items-start gap-3">
                  <span className="h-6 w-6 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">{step.step_number}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-neutral-900">{step.title}</p>
                    <div className="flex flex-wrap gap-3 text-xs text-neutral-500 my-1">
                      <span>👤 {step.responsible_role}</span>
                      <span>⏱ {step.timeline}</span>
                    </div>
                    <p className="text-sm text-neutral-700">{step.description}</p>
                    {step.tools_required.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {step.tools_required.map((t, i) => <span key={i} className="px-2 py-0.5 text-xs bg-neutral-200 text-neutral-700 rounded-full">{t}</span>)}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <button onClick={() => downloadWizardDocx(proc.title, [proc.framework], [], [proc])}
            className="flex items-center gap-2 text-xs text-secondary-600 hover:text-secondary-700 font-medium">
            <Download className="h-3.5 w-3.5" /> Download (.docx)
          </button>
        </div>
      )}
    </div>
  );
};

// ── Org history panel ─────────────────────────────────────────────────────────
const OrgHistoryPanel: React.FC<{ orgName: string; currentSessionId: number | null }> = ({ orgName, currentSessionId }) => {
  const { loadFromSession } = useWizardStore();
  const [sessions, setSessions] = useState<HistorySession[]>([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!orgName) return;
    historyApi.getByOrg(orgName, 10)
      .then((data) => setSessions(data.filter((s) => s.session_id !== currentSessionId)))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [orgName, currentSessionId]);

  const pastSessions = sessions;
  if (loading || pastSessions.length === 0) return null;

  return (
    <div className="border border-amber-200 rounded-xl overflow-hidden bg-amber-50">
      <button className="w-full flex items-center justify-between p-4 text-left"
        onClick={() => setOpen((o) => !o)}>
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-amber-600" />
          <span className="text-sm font-semibold text-amber-800">
            {pastSessions.length} previous generation{pastSessions.length > 1 ? 's' : ''} for {orgName}
          </span>
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-amber-600" /> : <ChevronRight className="h-4 w-4 text-amber-600" />}
      </button>
      {open && (
        <div className="border-t border-amber-200 divide-y divide-amber-100">
          {pastSessions.map((s) => (
            <div key={s.session_id} className="flex items-center justify-between px-4 py-3">
              <div className="min-w-0">
                <p className="text-xs text-neutral-500">{new Date(s.created_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</p>
                <div className="flex gap-1.5 mt-0.5 flex-wrap">
                  {s.selected_frameworks.map((fw) => <Badge key={fw} variant="info" size="sm">{fw}</Badge>)}
                  <span className="text-xs text-neutral-400">{s.policy_count} policies · {s.procedure_count} procedures</span>
                </div>
              </div>
              <Button variant="outline" size="sm" icon={<RotateCcw className="h-3.5 w-3.5" />}
                onClick={() => loadFromSession(s.session_id, s.org_name, s.org_description, s.selected_frameworks)}>
                Re-run
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ── Regenerate modal ──────────────────────────────────────────────────────────
const POLICY_TYPES_MAP: Record<string, string> = {
  data_protection: 'Data Protection & Privacy', incident_response: 'Incident Response',
  access_control: 'Access Control & IAM', data_retention: 'Data Retention',
  third_party_risk: 'Third-Party Risk', acceptable_use: 'Acceptable Use',
  business_continuity: 'Business Continuity', encryption: 'Encryption & Key Mgmt',
};
const PROC_TYPES_MAP: Record<string, string> = {
  incident_response: 'Incident Response', data_breach: 'Data Breach Notification',
  access_review: 'Access Review', vendor_assessment: 'Vendor Assessment',
  data_subject_request: 'Data Subject Request', risk_assessment: 'Risk Assessment',
  backup_recovery: 'Backup & Recovery', security_awareness: 'Security Awareness',
  change_management: 'Change Management', vulnerability_management: 'Vulnerability Mgmt',
};

const RegenerateModal: React.FC<{
  onClose: () => void;
  sessionId: number | null;
  frameworks: string[];
  onDone: (policies: GeneratedPolicy[], procedures: GeneratedProcedure[]) => void;
}> = ({ onClose, sessionId, frameworks, onDone }) => {
  const { selectedPolicyTypes, selectedProcedureTypes, answers } = useWizardStore();
  const [polTypes, setPolTypes] = useState<string[]>(selectedPolicyTypes);
  const [procTypes, setProcTypes] = useState<string[]>(selectedProcedureTypes);
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState<string[]>([]);

  const toggle = <T,>(arr: T[], val: T): T[] => arr.includes(val) ? arr.filter((x) => x !== val) : [...arr, val];

  const handleRegenerate = async () => {
    if (!sessionId) { toast.error('No session found'); return; }
    if (!polTypes.length && !procTypes.length) { toast.error('Select at least one type'); return; }
    setLoading(true);
    setLog(['Starting regeneration…']);
    try {
      const result = await historyApi.regenerate(sessionId, {
        frameworks,
        policy_types: polTypes,
        procedure_types: procTypes,
        org_context: answers as Record<string, string>,
      });
      setLog((l) => [...l, `✓ ${result.policy_count} policies, ${result.procedure_count} procedures generated`]);
      onDone(result.policies, result.procedures);
      toast.success('Regeneration complete');
      onClose();
    } catch (e: unknown) {
      setLog((l) => [...l, `✗ Failed: ${(e as Error).message}`]);
      toast.error('Regeneration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="p-6 border-b border-neutral-200">
          <h3 className="text-lg font-bold text-neutral-900">Regenerate Documents</h3>
          <p className="text-sm text-neutral-500 mt-1">Org info is saved — choose what to regenerate for {frameworks.join(', ')}.</p>
        </div>
        <div className="p-6 space-y-5">
          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Policies to regenerate</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(POLICY_TYPES_MAP).map(([k, v]) => (
                <button key={k} onClick={() => setPolTypes((p) => toggle(p, k))}
                  className={`text-left px-3 py-2 rounded-lg text-xs border transition-all ${polTypes.includes(k) ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-neutral-700 border-neutral-200 hover:border-primary-400'}`}>
                  {v}
                </button>
              ))}
            </div>
          </div>
          <div>
            <p className="text-sm font-semibold text-neutral-700 mb-2">Procedures to regenerate</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(PROC_TYPES_MAP).map(([k, v]) => (
                <button key={k} onClick={() => setProcTypes((p) => toggle(p, k))}
                  className={`text-left px-3 py-2 rounded-lg text-xs border transition-all ${procTypes.includes(k) ? 'bg-secondary-600 text-white border-secondary-600' : 'bg-white text-neutral-700 border-neutral-200 hover:border-secondary-400'}`}>
                  {v}
                </button>
              ))}
            </div>
          </div>
          {log.length > 0 && (
            <div className="bg-neutral-900 rounded-xl p-3 text-xs font-mono space-y-1 max-h-32 overflow-y-auto">
              {log.map((l, i) => <div key={i} className={l.startsWith('✓') ? 'text-green-400' : l.startsWith('✗') ? 'text-red-400' : 'text-neutral-300'}>{l}</div>)}
            </div>
          )}
        </div>
        <div className="p-6 border-t border-neutral-200 flex gap-3">
          <Button variant="primary" fullWidth onClick={handleRegenerate} disabled={loading}>
            {loading ? 'Regenerating…' : 'Regenerate Now'}
          </Button>
          <Button variant="outline" onClick={onClose} disabled={loading}>Cancel</Button>
        </div>
      </div>
    </div>
  );
};

// ── Main results page ─────────────────────────────────────────────────────────
export const StepResults: React.FC = () => {
  const { policies, procedures, orgName, selectedGenFrameworks, answers, questions, sessionId, setResults, reset } = useWizardStore();
  const [tab, setTab] = useState<'policies' | 'procedures'>('policies');
  const [downloading, setDownloading] = useState(false);
  const [showRegenerate, setShowRegenerate] = useState(false);

  const downloadAll = async () => {
    setDownloading(true);
    try {
      await downloadWizardDocx(orgName, selectedGenFrameworks, policies, procedures);
      toast.success('DOCX downloaded successfully');
    } catch {
      toast.error('Download failed — try again');
    } finally {
      setDownloading(false);
    }
  };

  const handleRegenDone = (newPolicies: GeneratedPolicy[], newProcs: GeneratedProcedure[]) => {
    setResults(
      // Replace by policy_type+framework (not policy_id — IDs repeat across runs)
      (() => {
        const merged = [...policies];
        for (const np of newPolicies) {
          const idx = merged.findIndex(
            (p) => p.policy_type === np.policy_type && p.framework === np.framework
          );
          if (idx >= 0) merged[idx] = np; else merged.push(np);
        }
        return merged;
      })(),
      (() => {
        const merged = [...procedures];
        for (const np of newProcs) {
          const idx = merged.findIndex(
            (p) => p.procedure_type === np.procedure_type && p.framework === np.framework
          );
          if (idx >= 0) merged[idx] = np; else merged.push(np);
        }
        return merged;
      })(),
    );
  };

  const answeredCount = Object.keys(answers).length;

  return (
    <div className="space-y-6">
      {/* Hero */}
      <div className="text-center space-y-2">
        <div className="text-4xl">🎉</div>
        <h2 className="text-2xl font-bold text-neutral-900">Documents Generated!</h2>
        <p className="text-neutral-500">
          {policies.length} policies · {procedures.length} procedures · {selectedGenFrameworks.join(', ')}
          {answeredCount > 0 && ` · ${answeredCount} personalizations applied`}
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Policies',   value: policies.length,   color: 'bg-primary-50 text-primary-700 border-primary-200' },
          { label: 'Procedures', value: procedures.length, color: 'bg-secondary-50 text-secondary-700 border-secondary-200' },
          { label: 'Frameworks', value: selectedGenFrameworks.length, color: 'bg-accent-50 text-accent-700 border-accent-200' },
        ].map(({ label, value, color }) => (
          <div key={label} className={`rounded-xl border p-4 text-center ${color}`}>
            <p className="text-2xl font-bold">{value}</p>
            <p className="text-xs font-medium mt-0.5">{label}</p>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex gap-3">
        <Button variant="primary" fullWidth size="lg" icon={<Download className="h-5 w-5" />}
          onClick={downloadAll} disabled={downloading}>
          {downloading ? 'Generating DOCX…' : 'Download All Documents (.docx)'}
        </Button>
        <Button variant="outline" size="lg" icon={<RefreshCw className="h-5 w-5" />}
          onClick={() => setShowRegenerate(true)} title="Regenerate without re-entering org info">
          Regenerate
        </Button>
      </div>

      {/* Org history */}
      {orgName && <OrgHistoryPanel orgName={orgName} currentSessionId={sessionId} />}

      {/* Personalization summary */}
      {answeredCount > 0 && (
        <Card>
          <CardHeader title="Personalization Details Used" />
          <CardBody>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {questions.filter((q) => answers[q.key]).map((q) => (
                <div key={q.key} className="text-xs">
                  <span className="font-medium text-neutral-700">{q.label}: </span>
                  <span className="text-neutral-600">{answers[q.key]}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex border-b border-neutral-200 gap-4">
        {(['policies', 'procedures'] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`pb-2 text-sm font-medium capitalize transition-colors border-b-2 ${tab === t ? 'text-primary-600 border-primary-600' : 'text-neutral-500 border-transparent hover:text-neutral-700'}`}>
            {t === 'policies' ? `📋 Policies (${policies.length})` : `📑 Procedures (${procedures.length})`}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="space-y-3 animate-fade-in">
        {tab === 'policies'
          ? policies.map((p, i) => <PolicyCard key={`${p.framework}-${p.policy_type}-${i}`} policy={p} />)
          : procedures.map((p, i) => <ProcedureCard key={`${p.framework}-${p.procedure_type}-${i}`} proc={p} />)
        }
        {tab === 'policies' && policies.length === 0 && <p className="text-center text-neutral-400 py-8">No policies generated.</p>}
        {tab === 'procedures' && procedures.length === 0 && (
          <div className="text-center py-8 space-y-3">
            <p className="text-neutral-400">No procedures generated yet.</p>
            <Button variant="outline" size="sm" icon={<RefreshCw className="h-4 w-4" />}
              onClick={() => setShowRegenerate(true)}>
              Generate Procedures Now
            </Button>
          </div>
        )}
      </div>

      {/* Start new run */}
      <div className="text-center pt-4">
        <Button variant="outline" icon={<RefreshCw className="h-4 w-4" />} onClick={reset}>
          Start New Compliance Run
        </Button>
      </div>

      {/* Regenerate modal */}
      {showRegenerate && (
        <RegenerateModal
          onClose={() => setShowRegenerate(false)}
          sessionId={sessionId}
          frameworks={selectedGenFrameworks}
          onDone={handleRegenDone}
        />
      )}
    </div>
  );
};
