'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardBody, CardHeader } from '../components/Card';
import { Badge } from '../components/Badge';
import { statusApi } from '@/api/status';
import { frameworksApi } from '@/api/frameworks';
import { useAuthStore } from '@/store/authStore';
import type { SystemStatus, Framework } from '@/types';
import Link from 'next/link';
import { ArrowLeft, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import { Button } from '../components/Button';

export default function SettingsPage(_props: PageProps<'/settings'>) {
  const router = useRouter();
  const { isAuthenticated, initializeFromStorage } = useAuthStore();
  const [status, setStatus]         = useState<SystemStatus | null>(null);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [loading, setLoading]       = useState(true);
  const [backendUp, setBackendUp]   = useState<boolean | null>(null);

  // Hydrate auth and guard the route
  useEffect(() => {
    initializeFromStorage();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth');
    }
  }, [isAuthenticated, router]);

  const load = async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    const up = await statusApi.health();
    setBackendUp(up);
    if (up) {
      try {
        const [s, fw] = await Promise.all([statusApi.get(), frameworksApi.list()]);
        setStatus(s);
        setFrameworks(fw);
      } catch { /* non-fatal */ }
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [isAuthenticated]);

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Simple header */}
      <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-neutral-200">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="sm" icon={<ArrowLeft className="h-4 w-4" />}>Back</Button>
          </Link>
          <div>
            <h1 className="text-lg font-bold text-neutral-900">Settings & Status</h1>
            <p className="text-xs text-neutral-500">Backend connection and framework registry</p>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-6">

        {/* Backend connection */}
        <Card>
          <CardHeader
            title="Backend Connection"
            action={
              <Button variant="ghost" size="sm" icon={<RefreshCw className="h-4 w-4" />} onClick={load} isLoading={loading}>
                Refresh
              </Button>
            }
          />
          <CardBody>
            <div className="flex items-center gap-3">
              {backendUp === null ? (
                <span className="text-sm text-neutral-400">Checking…</span>
              ) : backendUp ? (
                <>
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="text-sm font-medium text-green-700">Backend is online</span>
                </>
              ) : (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-sm font-medium text-red-700">Backend is offline — start the FastAPI server on port 8000</span>
                </>
              )}
            </div>

            {status && (
              <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { label: 'Status',      value: status.status },
                  { label: 'Groq Keys',   value: `${status.groq_keys} keys` },
                  { label: 'Groq Slots',  value: `${status.groq_total_slots} slots` },
                  { label: 'Tavily',      value: status.tavily_available ? 'Available' : 'Not configured' },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-neutral-50 rounded-lg p-3 border border-neutral-200">
                    <p className="text-xs text-neutral-500">{label}</p>
                    <p className="text-sm font-semibold text-neutral-900 mt-0.5">{value}</p>
                  </div>
                ))}
              </div>
            )}

            {status?.groq_models && (
              <div className="mt-3">
                <p className="text-xs text-neutral-500 mb-2">Groq Models in rotation</p>
                <div className="flex flex-wrap gap-2">
                  {status.groq_models.map((m) => (
                    <span key={m} className="px-2.5 py-1 text-xs bg-neutral-100 text-neutral-700 rounded-full border border-neutral-200">{m}</span>
                  ))}
                </div>
              </div>
            )}
          </CardBody>
        </Card>

        {/* API config */}
        <Card>
          <CardHeader title="Frontend Configuration" />
          <CardBody>
            <div className="space-y-3 text-sm">
              {[
                { label: 'Backend URL',    value: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000 (default)' },
                { label: 'API Timeout',    value: '120 seconds' },
                { label: 'Frontend Port',  value: '3000' },
              ].map(({ label, value }) => (
                <div key={label} className="flex items-center justify-between py-2 border-b border-neutral-100 last:border-0">
                  <span className="text-neutral-500">{label}</span>
                  <span className="font-mono text-xs bg-neutral-100 px-2 py-1 rounded text-neutral-800">{value}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-neutral-400 mt-3">
              Change <code className="bg-neutral-100 px-1 rounded">NEXT_PUBLIC_API_URL</code> in <code className="bg-neutral-100 px-1 rounded">frontend/.env.local</code> to point to a different backend.
            </p>
          </CardBody>
        </Card>

        {/* Supported frameworks */}
        {frameworks.length > 0 && (
          <Card>
            <CardHeader title={`Supported Frameworks (${frameworks.length})`} />
            <CardBody>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {frameworks.map((fw) => (
                  <div key={fw.id} className="flex items-start gap-3 p-3 rounded-lg bg-neutral-50 border border-neutral-200">
                    <span className="text-xl shrink-0">{fw.icon}</span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-neutral-900">{fw.id}</span>
                        <Badge variant="info" size="sm">{fw.region}</Badge>
                      </div>
                      <p className="text-xs text-neutral-500 mt-0.5 truncate">{fw.name}</p>
                      <p className="text-xs text-neutral-400 mt-0.5">Fine: {fw.max_fine}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        )}

        {/* How to run */}
        <Card>
          <CardHeader title="How to Run" />
          <CardBody>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-semibold text-neutral-800 mb-2">Start the backend</p>
                <pre className="bg-neutral-900 text-neutral-100 rounded-lg p-4 text-xs overflow-x-auto">
{`cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`}
                </pre>
              </div>
              <div>
                <p className="text-sm font-semibold text-neutral-800 mb-2">Start the frontend</p>
                <pre className="bg-neutral-900 text-neutral-100 rounded-lg p-4 text-xs overflow-x-auto">
{`cd frontend
npm run dev`}
                </pre>
              </div>
            </div>
          </CardBody>
        </Card>

      </div>
    </div>
  );
}
