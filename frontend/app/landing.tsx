'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardBody } from './components/Card';
import { Button } from './components/Button';
import { Zap, FileText } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

const WRITE_ROLES = ['admin', 'compliance_officer'];

export const LandingPage: React.FC = () => {
  const router = useRouter();
  const { user } = useAuthStore();

  useEffect(() => {
    useAuthStore.getState().initializeFromStorage();
  }, []);

  const canWrite = user?.role ? WRITE_ROLES.includes(user.role) : false;
  const greeting = user?.full_name ? `Welcome back, ${user.full_name}!` : 'Welcome to ComplianceIQ';

  return (
    <main className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-xl border-b border-neutral-200">
        <div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-primary-600 to-secondary-500 flex items-center justify-center text-white font-bold shadow-md text-base">
              ⚡
            </div>
            <div>
              <h1 className="text-sm font-bold text-neutral-900 leading-tight">ComplianceIQ</h1>
              <p className="text-xs text-neutral-500 hidden sm:block">AI-powered policy generation</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="max-w-2xl w-full space-y-8">
          {/* Welcome Section */}
          <div className="text-center space-y-3">
            <div className="text-5xl">🚀</div>
            <h1 className="text-3xl sm:text-4xl font-bold text-neutral-900">
              {greeting}
            </h1>
            <p className="text-neutral-600 text-lg">
              AI-powered compliance policies and procedures tailored to your organization
            </p>
          </div>

          {/* Action Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* New Scan Card — write roles only */}
            {canWrite && (
              <Card>
                <CardBody className="p-6 flex flex-col items-center text-center space-y-4 h-full justify-between">
                  <div>
                    <div className="text-4xl mb-3">✨</div>
                    <h2 className="text-lg font-bold text-neutral-900 mb-2">Start New Scan</h2>
                    <p className="text-sm text-neutral-600">
                      Generate personalized compliance documents for your organization
                    </p>
                  </div>
                  <Button
                    variant="primary"
                    onClick={() => router.push('/wizard')}
                    icon={<Zap className="h-4 w-4" />}
                    className="w-full"
                  >
                    Create New Policies
                  </Button>
                </CardBody>
              </Card>
            )}

            {/* History Card — all roles */}
            <Card>
              <CardBody className="p-6 flex flex-col items-center text-center space-y-4 h-full justify-between">
                <div>
                  <div className="text-4xl mb-3">📋</div>
                  <h2 className="text-lg font-bold text-neutral-900 mb-2">View History</h2>
                  <p className="text-sm text-neutral-600">
                    Access all past scans and generated compliance documents
                  </p>
                </div>
                <Button
                  variant="secondary"
                  onClick={() => router.push('/history')}
                  icon={<FileText className="h-4 w-4" />}
                  className="w-full"
                >
                  View Past Scans
                </Button>
              </CardBody>
            </Card>
          </div>

          {/* Features Section */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-neutral-700 uppercase tracking-wide">Features</h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  title: 'AI-Powered',
                  description: 'Advanced AI tailors policies to your organization',
                  icon: '🤖',
                },
                {
                  title: 'Multi-Framework',
                  description: 'Support for GDPR, HIPAA, PCI-DSS and more',
                  icon: '🔒',
                },
                {
                  title: 'Quick Export',
                  description: 'Download as professional DOCX documents',
                  icon: '📄',
                },
              ].map((feature) => (
                <div key={feature.title} className="p-4 rounded-lg bg-white border border-neutral-200">
                  <div className="text-2xl mb-2">{feature.icon}</div>
                  <p className="font-medium text-sm text-neutral-900">{feature.title}</p>
                  <p className="text-xs text-neutral-600 mt-1">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
};
