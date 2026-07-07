'use client';

import React from 'react';
import { CheckCircle2, Clock, Target } from 'lucide-react';
import type { ImplementationPhase } from '@/api/masterPolicy';

interface ImplementationRoadmapProps {
  phases: ImplementationPhase[];
}

/**
 * ImplementationRoadmap - Displays the phased implementation plan
 * Shows timeline, focus areas, and controls for each phase
 */
export const ImplementationRoadmap: React.FC<ImplementationRoadmapProps> = ({ phases }) => {
  if (!phases || phases.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-neutral-500 text-sm">No implementation phases available</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary-600 via-primary-400 to-secondary-400" />

        {/* Phases */}
        <div className="space-y-6">
          {phases.map((phase, idx) => (
            <div key={idx} className="relative pl-20">
              {/* Dot on timeline */}
              <div className="absolute left-0 top-1 h-12 w-12 rounded-full bg-white border-4 border-primary-600 flex items-center justify-center">
                <span className="text-xs font-bold text-primary-600">
                  {phase.phase}
                </span>
              </div>

              {/* Phase card */}
              <div className="bg-white border border-neutral-200 rounded-xl p-4 hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-semibold text-neutral-900 text-sm">
                      Phase {phase.phase}
                    </h4>
                    <p className="text-xs text-neutral-500 mt-0.5">{phase.duration}</p>
                  </div>
                  <div className="flex items-center gap-1 px-2 py-1 bg-primary-50 rounded-full">
                    <Clock className="h-3 w-3 text-primary-600" />
                    <span className="text-xs text-primary-700 font-medium">{phase.duration}</span>
                  </div>
                </div>

                {/* Focus */}
                <div className="mb-3 pb-3 border-b border-neutral-100">
                  <div className="flex items-start gap-2">
                    <Target className="h-4 w-4 text-secondary-600 mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-neutral-600">Focus Area</p>
                      <p className="text-sm text-neutral-900 mt-0.5">{phase.focus}</p>
                    </div>
                  </div>
                </div>

                {/* Controls */}
                <div>
                  <p className="text-xs font-medium text-neutral-600 mb-2">Controls & Initiatives</p>
                  <div className="space-y-1.5">
                    {phase.controls && phase.controls.length > 0 ? (
                      phase.controls.map((control, cidx) => (
                        <div
                          key={cidx}
                          className="flex items-start gap-2 px-2.5 py-1.5 bg-neutral-50 rounded-lg border border-neutral-150"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5 text-secondary-600 mt-0.5 shrink-0" />
                          <span className="text-xs text-neutral-800">{control}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-neutral-400 italic">No specific controls defined</p>
                    )}
                  </div>
                </div>

                {/* Progress indicator */}
                {idx === 0 && (
                  <div className="mt-4 pt-3 border-t border-neutral-100">
                    <div className="flex items-center gap-2 text-xs text-primary-700 font-medium">
                      <div className="h-2 w-2 rounded-full bg-primary-600" />
                      Recommended to start first
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs text-blue-900">
          <span className="font-semibold">Total Timeline:</span> Approximately{' '}
          {phases.length > 0 ? phases[phases.length - 1].duration : 'N/A'} for full implementation
        </p>
      </div>
    </div>
  );
};
