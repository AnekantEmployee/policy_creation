'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '../components/Header';
import { Card, CardBody } from '../components/Card';
import { Badge } from '../components/Badge';
import { Button } from '../components/Button';
import { historyApi } from '@/api/history';
import { downloadSessionDocx } from '@/api/export';
import { useWizardStore } from '@/store/wizardStore';
import { useAuthStore } from '@/store/authStore';
import type { HistorySession, SessionDetail } from '@/types';
import { formatDateTime } from '@/lib/utils';
import { ChevronDown, ChevronRight, Trash2, Download, FileText, Zap, RotateCcw } from 'lucide-react';
import toast from 'react-hot-toast';

// Roles that are allowed to delete sessions or re-run scans
const WRITE_ROLES = ['admin', 'compliance_officer'];

export default function HistoryPage(_props: PageProps<'/history'>) {
  const router = useRouter();
  const { loadFromSession } = useWizardStore();
  const { user, isAuthenticated, initializeFromStorage } = useAuthStore();

  const [sessions, setSessions]         = useState<HistorySession[]>([]);
  const [loading, setLoading]           = useState(true);
  const [expanded, setExpanded]         = useState<number | null>(null);
  const [detail, setDetail]             = useState<SessionDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [downloading, setDownloading]   = useState<number | null>(null);
  const [expandedOrgs, setExpandedOrgs] = useState<Set<string>>(new Set());
  const [hydrated, setHydrated] = useState(false);
  const alphabetRef = useRef<HTMLDivElement>(null);
  const orgSectionsRef = useRef<Record<string, HTMLDivElement | null>>({});

  // Hydrate auth from storage on mount
  useEffect(() => {
    initializeFromStorage();
    setHydrated(true);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Redirect to auth if not authenticated (after hydration is complete)
  useEffect(() => {
    if (hydrated && !isAuthenticated) {
      router.push('/auth');
    }
  }, [hydrated, isAuthenticated, router]);

  const canWrite = user?.role ? WRITE_ROLES.includes(user.role) : false;

  // ── Load sessions list ──────────────────────────────────────────────────
  const load = async () => {
    setLoading(true);
    try {
      const data = await historyApi.list(100);
      setSessions(data);
    } catch (e: any) {
      console.error('Failed to load history:', e);
      // If auth failed (401), clear auth and redirect
      if (e?.response?.status === 401) {
        console.log('Auth token invalid, clearing and redirecting');
        useAuthStore.getState().clearAuth();
        router.push('/auth');
        return;
      }
      toast.error('Failed to load history');
      setSessions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    if (hydrated && isAuthenticated) {
      load();
    }
  }, [hydrated, isAuthenticated]);

  // ── Expand / collapse a session row ────────────────────────────────────
  const handleExpand = async (id: number) => {
    if (expanded === id) { setExpanded(null); setDetail(null); return; }
    setExpanded(id);
    setDetail(null);
    setDetailLoading(true);
    try {
      const d = await historyApi.get(id);
      setDetail(d);
    } catch {
      toast.error('Failed to load session detail');
    } finally {
      setDetailLoading(false);
    }
  };

  // ── Re-run from history ──────────────────────────────────────────────────
  const handleReRun = (s: HistorySession) => {
    if (!canWrite) {
      toast.error('Your role does not have permission to generate new scans');
      return;
    }
    loadFromSession(s.session_id, s.org_name, s.org_description, s.selected_frameworks);
    router.push('/');
    toast.success(`Loaded ${s.org_name} — choose docs and regenerate`);
  };

  // ── Delete a session ────────────────────────────────────────────────────
  const handleDelete = async (id: number) => {
    if (!canWrite) {
      toast.error('Your role does not have permission to delete sessions');
      return;
    }
    try {
      await historyApi.delete(id);
      setSessions((s) => s.filter((x) => x.session_id !== id));
      if (expanded === id) { setExpanded(null); setDetail(null); }
      toast.success('Session deleted');
    } catch {
      toast.error('Failed to delete session');
    }
  };

  // ── Download session as DOCX ────────────────────────────────────────────
  const handleDownloadDocx = async (s: HistorySession) => {
    setDownloading(s.session_id);
    try {
      await downloadSessionDocx(s.session_id, s.org_name);
      toast.success('DOCX downloaded');
    } catch {
      toast.error('Export failed — try again');
    } finally {
      setDownloading(null);
    }
  };

  const totalPolicies   = sessions.reduce((a, s) => a + s.policy_count,    0);
  const totalProcedures = sessions.reduce((a, s) => a + s.procedure_count, 0);

  // Group sessions by organization (case-insensitive) and then by date
  const groupedByOrg = sessions.reduce((acc, session) => {
    const orgKey = session.org_name.toLowerCase();
    if (!acc[orgKey]) {
      acc[orgKey] = { displayName: session.org_name, sessions: [] };
    }
    acc[orgKey].sessions.push(session);
    return acc;
  }, {} as Record<string, { displayName: string; sessions: HistorySession[] }>);

  // Sort organizations alphabetically
  const sortedOrgs = Object.keys(groupedByOrg).sort();

  // Get all alphabets A-Z and mark available ones
  const allAlphabets = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const availableLetters = new Set(sortedOrgs.map(org => org.charAt(0).toUpperCase()));

  const handleAlphabetClick = (letter: string) => {
    const firstOrgWithLetter = sortedOrgs.find(org => org.charAt(0).toUpperCase() === letter);
    if (firstOrgWithLetter && orgSectionsRef.current[firstOrgWithLetter]) {
      orgSectionsRef.current[firstOrgWithLetter]?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const toggleOrgExpanded = (orgKey: string) => {
    const newExpanded = new Set(expandedOrgs);
    if (newExpanded.has(orgKey)) {
      newExpanded.delete(orgKey);
    } else {
      newExpanded.add(orgKey);
    }
    setExpandedOrgs(newExpanded);
  };

  return (
    <main className="min-h-screen bg-neutral-50">
      <Header title="History" subtitle="All past compliance sessions" />

      <div className="p-6 space-y-6 flex flex-col lg:flex-row gap-6">

        {/* Alphabet Scroller - visible on larger screens */}
        {!loading && sessions.length > 0 && (
          <div className="hidden lg:flex flex-col gap-1 sticky top-24 h-fit">
            <p className="text-xs font-semibold text-neutral-400 uppercase tracking-wide mb-2">Organizations</p>
            <div ref={alphabetRef} className="flex flex-col gap-0.5">
              {allAlphabets.map((letter) => {
                const isAvailable = availableLetters.has(letter);
                return (
                  <button
                    key={letter}
                    onClick={() => isAvailable && handleAlphabetClick(letter)}
                    disabled={!isAvailable}
                    className={`w-8 h-8 text-xs font-semibold rounded transition-colors ${
                      isAvailable
                        ? 'text-neutral-600 hover:bg-primary-100 hover:text-primary-700 cursor-pointer'
                        : 'text-neutral-300 bg-neutral-100 cursor-not-allowed'
                    }`}
                  >
                    {letter}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 space-y-6">

          {/* ── Stats ── */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Sessions',   value: sessions.length  },
              { label: 'Policies',   value: totalPolicies    },
              { label: 'Procedures', value: totalProcedures  },
            ].map(({ label, value }) => (
              <Card key={label}>
                <CardBody className="p-4 text-center">
                  <p className="text-2xl font-bold text-neutral-900">{value}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">{label}</p>
                </CardBody>
              </Card>
            ))}
          </div>

          {/* ── Loading skeleton ── */}
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-16 rounded-xl bg-neutral-200 animate-pulse" />
              ))}
            </div>

          /* ── Empty state ── */
          ) : sessions.length === 0 ? (
            <Card>
              <CardBody className="flex flex-col items-center py-20 gap-3 text-center">
                <span className="text-4xl">🗂️</span>
                <p className="font-semibold text-neutral-700">No sessions yet</p>
                <p className="text-sm text-neutral-500">
                  Generate your first compliance documents to see them here
                </p>
                <a href="/"><Button variant="primary">Start a New Run</Button></a>
              </CardBody>
            </Card>

          /* ── Organized by Organization ── */
          ) : (
            <div className="space-y-6">
              {sortedOrgs.map((orgKey) => {
                const orgData = groupedByOrg[orgKey];
                const orgSessions = orgData.sessions;
                const orgName = orgData.displayName;
                // Sort sessions by date (newest first)
                const sortedSessions = [...orgSessions].sort((a, b) => 
                  new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                );
                const isExpanded = expandedOrgs.has(orgKey);
                const totalOrgPolicies = orgSessions.reduce((a, s) => a + s.policy_count, 0);
                const totalOrgProcedures = orgSessions.reduce((a, s) => a + s.procedure_count, 0);

                return (
                  <div
                    key={orgKey}
                    ref={(el) => {
                      if (el) orgSectionsRef.current[orgKey] = el;
                    }}
                    className="scroll-mt-24"
                  >
                    {/* Organization Header */}
                    <div
                      className="flex items-center justify-between p-4 cursor-pointer hover:bg-neutral-100 rounded-lg transition-colors mb-3"
                      onClick={() => toggleOrgExpanded(orgKey)}
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded
                          ? <ChevronDown className="h-5 w-5 text-primary-600" />
                          : <ChevronRight className="h-5 w-5 text-neutral-400" />}
                        <div>
                          <p className="font-bold text-lg text-neutral-900">{orgName}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-neutral-400">{orgSessions.length} scan{orgSessions.length !== 1 ? 's' : ''}</span>
                            {totalOrgPolicies > 0 && (
                              <Badge variant="primary" size="sm">{totalOrgPolicies} policies</Badge>
                            )}
                            {totalOrgProcedures > 0 && (
                              <Badge variant="secondary" size="sm">{totalOrgProcedures} procedures</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Organization Sessions - Grouped by Date */}
                    {isExpanded && (
                      <div className="space-y-4 ml-4">
                        {sortedSessions.map((s) => (
                          <Card key={s.session_id} padding="none">

                            {/* Row header */}
                            <div
                              className="flex items-center justify-between p-4 cursor-pointer hover:bg-neutral-50 rounded-xl transition-colors"
                              onClick={() => handleExpand(s.session_id)}
                            >
                              <div className="flex items-center gap-3 min-w-0">
                                {expanded === s.session_id
                                  ? <ChevronDown  className="h-4 w-4 text-neutral-400 shrink-0" />
                                  : <ChevronRight className="h-4 w-4 text-neutral-400 shrink-0" />}
                                <div className="min-w-0">
                                  <p className="text-sm text-neutral-500">{formatDateTime(s.created_at)}</p>
                                  <div className="flex items-center flex-wrap gap-2 mt-0.5">
                                    {s.policy_count > 0 && (
                                      <Badge variant="primary"   size="sm">{s.policy_count} policies</Badge>
                                    )}
                                    {s.procedure_count > 0 && (
                                      <Badge variant="secondary" size="sm">{s.procedure_count} procedures</Badge>
                                    )}
                                    {/* Show selected frameworks, fall back to recommended */}
                                    {(s.selected_frameworks.length > 0
                                      ? s.selected_frameworks
                                      : s.recommended_frameworks?.slice(0, 3).map((f) => f.id) ?? []
                                    ).map((fw) => (
                                      <Badge key={fw} variant="info" size="sm">{fw}</Badge>
                                    ))}
                                  </div>
                                </div>
                              </div>

                              {/* Actions */}
                              <div className="flex items-center gap-1 ml-3 shrink-0" onClick={(e) => e.stopPropagation()}>
                                {/* Re-run button — write roles only */}
                                {canWrite && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    icon={<RotateCcw className="h-3.5 w-3.5 text-primary-500" />}
                                    onClick={() => handleReRun(s)}
                                    title="Re-run for this org"
                                  />
                                )}
                                {/* Download DOCX — all roles */}
                                {(s.policy_count > 0 || s.procedure_count > 0) && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    icon={<Download className="h-3.5 w-3.5" />}
                                    disabled={downloading === s.session_id}
                                    onClick={() => handleDownloadDocx(s)}
                                    title="Download as DOCX"
                                  />
                                )}
                                {/* Delete — write roles only */}
                                {canWrite && (
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    icon={<Trash2 className="h-3.5 w-3.5 text-red-400" />}
                                    onClick={() => handleDelete(s.session_id)}
                                    title="Delete session"
                                  />
                                )}
                              </div>
                            </div>

                            {/* ── Expanded detail ── */}
                            {expanded === s.session_id && (
                              <div className="border-t border-neutral-200 p-4 space-y-4 animate-fade-in">

                                {detailLoading && !detail && (
                                  <div className="flex justify-center py-8">
                                    <span className="text-sm text-neutral-400">Loading session detail…</span>
                                  </div>
                                )}

                                {detail && detail.session_id === s.session_id && (
                                  <>
                                    {/* Summary */}
                                    {detail.summary && (
                                      <p className="text-sm text-neutral-600 bg-neutral-50 rounded-lg p-3">
                                        {detail.summary}
                                      </p>
                                    )}

                                    {/* Org metadata */}
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                                      {([
                                        ['Country',    detail.org_country  ?? '—'],
                                        ['Website',    detail.org_website  ?? '—'],
                                        ['Industries', (detail.industries  ?? []).join(', ') || '—'],
                                        ['Regions',    (detail.regions     ?? []).join(', ') || '—'],
                                      ] as [string, string][]).map(([label, val]) => (
                                        <div key={label} className="bg-neutral-50 rounded-lg p-2">
                                          <p className="text-neutral-500 mb-0.5">{label}</p>
                                          <p className="font-medium text-neutral-800 truncate">{val}</p>
                                        </div>
                                      ))}
                                    </div>

                                    {/* Policies and Procedures - grouped by framework */}
                                    {(detail.policies.length > 0 || detail.procedures.length > 0) && (
                                      <>
                                        {/* Policies by framework */}
                                        {detail.policies.length > 0 && (
                                          <div>
                                            <p className="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                                              <FileText className="h-3.5 w-3.5" />
                                              Policies by Framework
                                            </p>
                                            <div className="space-y-3">
                                              {(() => {
                                                const frameworkGroups = detail.policies.reduce((acc, p) => {
                                                  if (!acc[p.framework]) acc[p.framework] = [];
                                                  acc[p.framework].push(p);
                                                  return acc;
                                                }, {} as Record<string, typeof detail.policies>);
                                                return Object.keys(frameworkGroups).sort().map((fw) => (
                                                  <div key={`policies-${fw}`}>
                                                    <div className="flex items-center gap-2 mb-1.5">
                                                      <Badge variant="primary" size="sm">{fw}</Badge>
                                                      <span className="text-xs text-neutral-400">({frameworkGroups[fw].length})</span>
                                                    </div>
                                                    <div className="space-y-1 ml-2">
                                                      {frameworkGroups[fw].map((p, idx) => (
                                                        <div key={`${p.policy_id}-${fw}-${idx}`} className="flex items-center justify-between py-2 px-3 bg-neutral-50 rounded-lg text-sm">
                                                          <span className="font-medium text-neutral-900 truncate">{p.title}</span>
                                                          <Badge variant="info" size="sm">v{p.version}</Badge>
                                                        </div>
                                                      ))}
                                                    </div>
                                                  </div>
                                                ));
                                              })()}
                                            </div>
                                          </div>
                                        )}

                                        {/* Procedures by framework */}
                                        {detail.procedures.length > 0 && (
                                          <div>
                                            <p className="text-xs font-semibold text-neutral-700 uppercase tracking-wide mb-2 flex items-center gap-1.5">
                                              <Zap className="h-3.5 w-3.5" />
                                              Procedures by Framework
                                            </p>
                                            <div className="space-y-3">
                                              {(() => {
                                                const frameworkGroups = detail.procedures.reduce((acc, p) => {
                                                  if (!acc[p.framework]) acc[p.framework] = [];
                                                  acc[p.framework].push(p);
                                                  return acc;
                                                }, {} as Record<string, typeof detail.procedures>);
                                                return Object.keys(frameworkGroups).sort().map((fw) => (
                                                  <div key={`procedures-${fw}`}>
                                                    <div className="flex items-center gap-2 mb-1.5">
                                                      <Badge variant="secondary" size="sm">{fw}</Badge>
                                                      <span className="text-xs text-neutral-400">({frameworkGroups[fw].length})</span>
                                                    </div>
                                                    <div className="space-y-1 ml-2">
                                                      {frameworkGroups[fw].map((p, idx) => (
                                                        <div key={`${p.procedure_id}-${fw}-${idx}`} className="flex items-center justify-between py-2 px-3 bg-neutral-50 rounded-lg text-sm">
                                                          <span className="font-medium text-neutral-900 truncate">{p.title}</span>
                                                          <span className="text-xs text-neutral-400">{p.frequency}</span>
                                                        </div>
                                                      ))}
                                                    </div>
                                                  </div>
                                                ));
                                              })()}
                                            </div>
                                          </div>
                                        )}

                                        {/* Download button */}
                                        <Button
                                          variant="primary"
                                          size="sm"
                                          icon={<Download className="h-4 w-4" />}
                                          disabled={downloading === s.session_id}
                                          onClick={() => handleDownloadDocx(s)}
                                        >
                                          {downloading === s.session_id
                                            ? 'Generating…'
                                            : 'Download Compliance Package (.docx)'}
                                        </Button>
                                      </>
                                    )}

                                    {/* No docs yet */}
                                    {detail.policies.length === 0 && detail.procedures.length === 0 && (
                                      <p className="text-sm text-neutral-400 text-center py-4">
                                        No documents generated for this session yet.
                                      </p>
                                    )}
                                  </>
                                )}
                              </div>
                            )}

                          </Card>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

        </div>

      </div>
    </main>
  );
}
