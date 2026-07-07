'use client';

import React from 'react';
import { Badge } from './Badge';
import { Card, CardBody, CardHeader } from './Card';
import { Crown, FileText } from 'lucide-react';
import type { MasterPolicyResponse } from '@/api/masterPolicy';

interface MasterPolicyCardProps {
  masterPolicy: MasterPolicyResponse | null;
  isLoading?: boolean;
  onDownload?: () => void;
  onConsolidate?: () => void;
}

/**
 * MasterPolicyCard - Displays a summary card of the master policy
 * Shows title, frameworks, domain count, and quick actions
 */
export const MasterPolicyCard: React.FC<MasterPolicyCardProps> = ({
  masterPolicy,
  isLoading = false,
  onDownload,
  onConsolidate,
}) => {
  if (isLoading) {
    return (
      <div className="border-2 border-dashed border-primary-200 rounded-xl p-6 bg-primary-50">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-primary-200 animate-pulse" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-primary-700">Consolidating policies...</p>
            <p className="text-xs text-primary-600 mt-1">Creating your unified master policy</p>
          </div>
        </div>
      </div>
    );
  }

  if (!masterPolicy) {
    return (
      <div className="border border-neutral-200 rounded-xl p-6 bg-neutral-50">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-neutral-700">No Master Policy Yet</p>
            <p className="text-xs text-neutral-500 mt-1">
              Create a consolidated policy from your selected frameworks
            </p>
          </div>
          {onConsolidate && (
            <button
              onClick={onConsolidate}
              className="px-3 py-1.5 text-xs font-medium bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors whitespace-nowrap"
            >
              Consolidate Now
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <Card className="border-2 border-primary-200 bg-gradient-to-br from-primary-50 to-blue-50">
      <div className="flex items-start justify-between p-6">
        <div className="flex items-start gap-4 flex-1 min-w-0">
          {/* Icon */}
          <div className="h-12 w-12 rounded-xl bg-primary-600 flex items-center justify-center shrink-0">
            <Crown className="h-6 w-6 text-white" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold text-primary-900 truncate">
                  {masterPolicy.title}
                </h3>
                <p className="text-xs text-primary-600 mt-1">
                  Master Policy v{masterPolicy.version}
                </p>
              </div>
            </div>

            {/* Frameworks */}
            <div className="flex flex-wrap gap-1.5 mt-3">
              {masterPolicy.aligned_frameworks.map((fw) => (
                <Badge key={fw} variant="primary" size="sm">
                  {fw}
                </Badge>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-4">
              <div className="bg-white/50 rounded-lg p-2.5 border border-primary-200">
                <p className="text-xs text-primary-600 font-medium">Domains</p>
                <p className="text-lg font-bold text-primary-900 mt-0.5">
                  {masterPolicy.domains.length}
                </p>
              </div>
              <div className="bg-white/50 rounded-lg p-2.5 border border-primary-200">
                <p className="text-xs text-primary-600 font-medium">Requirements</p>
                <p className="text-lg font-bold text-primary-900 mt-0.5">
                  {masterPolicy.domains.reduce((sum, d) => sum + d.integrated_requirements.length, 0)}
                </p>
              </div>
              <div className="bg-white/50 rounded-lg p-2.5 border border-primary-200">
                <p className="text-xs text-primary-600 font-medium">Frameworks</p>
                <p className="text-lg font-bold text-primary-900 mt-0.5">
                  {masterPolicy.aligned_frameworks.length}
                </p>
              </div>
              <div className="bg-white/50 rounded-lg p-2.5 border border-primary-200">
                <p className="text-xs text-primary-600 font-medium">Controls</p>
                <p className="text-lg font-bold text-primary-900 mt-0.5">
                  {masterPolicy.compliance_matrix.length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Button */}
        {onDownload && (
          <button
            onClick={onDownload}
            className="ml-4 px-4 py-2 bg-primary-600 text-white text-xs font-semibold rounded-lg hover:bg-primary-700 transition-colors whitespace-nowrap flex items-center gap-2 shrink-0"
            title="Download master policy as DOCX"
          >
            <FileText className="h-4 w-4" />
            Download
          </button>
        )}
      </div>

      {/* Executive Summary Preview */}
      {masterPolicy.executive_summary && (
        <div className="px-6 pb-6 border-t border-primary-100 pt-4">
          <p className="text-xs font-semibold text-primary-700 uppercase tracking-wide mb-2">
            Executive Summary
          </p>
          <p className="text-sm text-neutral-700 line-clamp-3">
            {masterPolicy.executive_summary}
          </p>
        </div>
      )}
    </Card>
  );
};
