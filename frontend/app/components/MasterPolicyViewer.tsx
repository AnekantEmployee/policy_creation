'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Shield, FileText } from 'lucide-react';
import { Badge } from './Badge';
import type { ConsolidatedDomain, ConsolidatedRequirement, MasterPolicyResponse } from '@/api/masterPolicy';

interface MasterPolicyViewerProps {
  masterPolicy: MasterPolicyResponse;
}

/**
 * RequirementDetail - Shows a single integrated requirement
 */
const RequirementDetail: React.FC<{ requirement: ConsolidatedRequirement }> = ({ requirement }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-neutral-200 rounded-lg p-4 hover:bg-neutral-50 transition-colors">
      <div
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="h-8 w-8 rounded-lg bg-primary-100 flex items-center justify-center shrink-0 mt-0.5">
            <Shield className="h-4 w-4 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-neutral-900 text-sm">{requirement.title}</p>
            <p className="text-xs text-neutral-500 mt-1">{requirement.requirement_id}</p>
          </div>
        </div>
        {expanded ? (
          <ChevronDown className="h-4 w-4 text-neutral-400 shrink-0 mt-1" />
        ) : (
          <ChevronRight className="h-4 w-4 text-neutral-400 shrink-0 mt-1" />
        )}
      </div>

      {expanded && (
        <div className="mt-4 pt-4 border-t border-neutral-200 space-y-4 animate-fade-in">
          {/* Description */}
          <div>
            <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">Description</p>
            <p className="text-sm text-neutral-700 whitespace-pre-wrap">{requirement.description}</p>
          </div>

          {/* Frameworks */}
          <div>
            <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">Applicable Frameworks</p>
            <div className="flex flex-wrap gap-1.5">
              {requirement.frameworks.map((fw) => (
                <Badge key={fw} variant="primary" size="sm">
                  {fw}
                </Badge>
              ))}
            </div>
          </div>

          {/* Framework References */}
          {requirement.framework_references.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
                Framework References
              </p>
              <div className="space-y-1">
                {requirement.framework_references.map((ref, idx) => (
                  <div key={idx} className="px-3 py-1.5 bg-neutral-100 rounded-lg border border-neutral-200">
                    <code className="text-xs text-neutral-700 font-mono">{ref}</code>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Meta Information */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-neutral-50 rounded-lg p-3 border border-neutral-200">
              <p className="text-xs text-neutral-600 mb-1">Mandatory</p>
              <p className="text-sm font-semibold text-neutral-900">
                {requirement.is_mandatory ? '✓ Yes' : '○ No'}
              </p>
            </div>
            <div className="bg-neutral-50 rounded-lg p-3 border border-neutral-200">
              <p className="text-xs text-neutral-600 mb-1">Responsibility</p>
              <p className="text-sm font-semibold text-neutral-900 truncate">{requirement.responsibility}</p>
            </div>
          </div>

          {/* Implementation Steps */}
          {requirement.implementation_steps.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-neutral-600 uppercase tracking-wide mb-2">
                Implementation Steps
              </p>
              <ol className="space-y-2">
                {requirement.implementation_steps.map((step, idx) => (
                  <li key={idx} className="flex gap-2 text-sm text-neutral-700">
                    <span className="h-6 w-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-xs shrink-0">
                      {idx + 1}
                    </span>
                    <span className="mt-0.5">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Max Penalty */}
          {requirement.max_penalty && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-xs text-red-700 font-medium">Maximum Penalty for Non-Compliance</p>
              <p className="text-sm text-red-900 font-semibold mt-1">{requirement.max_penalty}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * DomainSection - Shows a domain with its integrated requirements
 */
const DomainSection: React.FC<{ domain: ConsolidatedDomain }> = ({ domain }) => {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="border border-neutral-200 rounded-xl overflow-hidden">
      <div
        className="bg-gradient-to-r from-primary-50 to-blue-50 px-6 py-4 flex items-center justify-between cursor-pointer hover:from-primary-100 hover:to-blue-100 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-primary-600" />
          <div>
            <h3 className="font-semibold text-neutral-900">{domain.domain_name}</h3>
            <p className="text-xs text-neutral-500 mt-1">{domain.integrated_requirements.length} integrated requirements</p>
          </div>
        </div>
        {expanded ? (
          <ChevronDown className="h-5 w-5 text-primary-600 shrink-0" />
        ) : (
          <ChevronRight className="h-5 w-5 text-primary-600 shrink-0" />
        )}
      </div>

      {expanded && (
        <div className="p-6 space-y-3 animate-fade-in border-t border-neutral-200">
          {/* Domain Description */}
          {domain.domain_description && (
            <p className="text-sm text-neutral-600 italic mb-4 p-3 bg-neutral-50 rounded-lg">
              {domain.domain_description}
            </p>
          )}

          {/* Requirements */}
          <div className="space-y-3">
            {domain.integrated_requirements.map((req, idx) => (
              <RequirementDetail key={idx} requirement={req} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * MasterPolicyViewer - Full master policy display with all domains and requirements
 */
export const MasterPolicyViewer: React.FC<MasterPolicyViewerProps> = ({ masterPolicy }) => {
  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-xl p-6">
        <h2 className="text-2xl font-bold text-neutral-900">{masterPolicy.title}</h2>
        <p className="text-sm text-neutral-600 mt-2">Version {masterPolicy.version}</p>

        {/* Frameworks Badges */}
        <div className="flex flex-wrap gap-2 mt-4">
          {masterPolicy.aligned_frameworks.map((fw) => (
            <Badge key={fw} variant="primary" size="sm">
              {fw}
            </Badge>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="bg-white/50 rounded-lg p-3 border border-primary-200">
            <p className="text-xs text-primary-600 font-medium">Domains</p>
            <p className="text-2xl font-bold text-primary-900 mt-1">{masterPolicy.domains.length}</p>
          </div>
          <div className="bg-white/50 rounded-lg p-3 border border-primary-200">
            <p className="text-xs text-primary-600 font-medium">Total Requirements</p>
            <p className="text-2xl font-bold text-primary-900 mt-1">
              {masterPolicy.domains.reduce((sum, d) => sum + d.integrated_requirements.length, 0)}
            </p>
          </div>
          <div className="bg-white/50 rounded-lg p-3 border border-primary-200">
            <p className="text-xs text-primary-600 font-medium">Controls</p>
            <p className="text-2xl font-bold text-primary-900 mt-1">{masterPolicy.compliance_matrix.length}</p>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      {masterPolicy.executive_summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="font-semibold text-neutral-900 mb-3">Executive Summary</h3>
          <p className="text-sm text-neutral-700 whitespace-pre-wrap">{masterPolicy.executive_summary}</p>
        </div>
      )}

      {/* Consolidation Notes */}
      {masterPolicy.consolidation_notes && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
          <h3 className="font-semibold text-neutral-900 mb-3">Consolidation Approach</h3>
          <p className="text-sm text-neutral-700 whitespace-pre-wrap">{masterPolicy.consolidation_notes}</p>
        </div>
      )}

      {/* Domains */}
      <div>
        <h3 className="font-semibold text-lg text-neutral-900 mb-4">Compliance Domains</h3>
        <div className="space-y-4">
          {masterPolicy.domains.map((domain, idx) => (
            <DomainSection key={idx} domain={domain} />
          ))}
        </div>
      </div>
    </div>
  );
};
