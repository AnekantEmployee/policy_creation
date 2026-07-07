'use client';

import React, { useState } from 'react';
import { Crown, BarChart3, Map, Grid3x3 } from 'lucide-react';
import { MasterPolicyViewer } from './MasterPolicyViewer';
import { ComplianceMatrix } from './ComplianceMatrix';
import { ImplementationRoadmap } from './ImplementationRoadmap';
import type { MasterPolicyResponse } from '@/api/masterPolicy';

type TabType = 'policy' | 'matrix' | 'roadmap';

interface MasterPolicyTabsProps {
  masterPolicy: MasterPolicyResponse;
}

/**
 * MasterPolicyTabs - Tab component to view different aspects of the master policy
 * - Policy: Full domain-based master policy
 * - Compliance Matrix: Framework vs control matrix
 * - Implementation Roadmap: Phased rollout plan
 */
export const MasterPolicyTabs: React.FC<MasterPolicyTabsProps> = ({ masterPolicy }) => {
  const [activeTab, setActiveTab] = useState<TabType>('policy');

  const tabs: Array<{ id: TabType; label: string; icon: React.ReactNode; count?: number }> = [
    {
      id: 'policy',
      label: 'Master Policy',
      icon: <Crown className="h-4 w-4" />,
      count: masterPolicy.domains.length,
    },
    {
      id: 'matrix',
      label: 'Compliance Matrix',
      icon: <Grid3x3 className="h-4 w-4" />,
      count: masterPolicy.compliance_matrix.length,
    },
    {
      id: 'roadmap',
      label: 'Implementation Plan',
      icon: <Map className="h-4 w-4" />,
      count: masterPolicy.implementation_roadmap.length,
    },
  ];

  return (
    <div className="space-y-0">
      {/* Tab Navigation */}
      <div className="border-b border-neutral-200 bg-white rounded-t-xl overflow-x-auto">
        <div className="flex gap-0 min-w-min p-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all whitespace-nowrap ${
                activeTab === tab.id
                  ? 'text-primary-600 border-b-primary-600 bg-primary-50'
                  : 'text-neutral-600 border-b-transparent hover:text-neutral-900 hover:bg-neutral-50'
              }`}
            >
              {tab.icon}
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={`ml-1 px-2 py-0.5 text-xs rounded-full font-semibold ${
                    activeTab === tab.id
                      ? 'bg-primary-200 text-primary-700'
                      : 'bg-neutral-200 text-neutral-700'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-b-xl border border-t-0 border-neutral-200 p-6 animate-fade-in">
        {activeTab === 'policy' && <MasterPolicyViewer masterPolicy={masterPolicy} />}

        {activeTab === 'matrix' && (
          <ComplianceMatrix
            matrix={masterPolicy.compliance_matrix}
            frameworks={masterPolicy.aligned_frameworks}
          />
        )}

        {activeTab === 'roadmap' && (
          <ImplementationRoadmap phases={masterPolicy.implementation_roadmap} />
        )}
      </div>
    </div>
  );
};
