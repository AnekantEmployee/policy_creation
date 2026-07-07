'use client';

import React, { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import type { ComplianceMatrixRow } from '@/api/masterPolicy';

interface ComplianceMatrixProps {
  matrix: ComplianceMatrixRow[];
  frameworks: string[];
}

/**
 * ComplianceMatrix - Displays a table showing which frameworks require which controls
 * Shows control names and their requirement status per framework
 */
export const ComplianceMatrix: React.FC<ComplianceMatrixProps> = ({ matrix, frameworks }) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter controls based on search
  const filteredMatrix = useMemo(() => {
    if (!searchTerm.trim()) return matrix;
    return matrix.filter((row) =>
      row.control_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [matrix, searchTerm]);

  // Get status badge color
  const getStatusColor = (status: string): string => {
    const s = status?.toLowerCase() || '';
    if (s === 'mandatory' || s === 'required') return 'bg-red-100 text-red-700 border-red-300';
    if (s === 'recommended') return 'bg-yellow-100 text-yellow-700 border-yellow-300';
    if (s === 'optional') return 'bg-blue-100 text-blue-700 border-blue-300';
    return 'bg-neutral-100 text-neutral-700 border-neutral-300';
  };

  if (matrix.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-neutral-500 text-sm">No compliance controls found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-neutral-400" />
        <input
          type="text"
          placeholder="Search controls..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-neutral-200 rounded-lg">
        <table className="w-full">
          <thead>
            <tr className="bg-neutral-50 border-b border-neutral-200">
              <th className="px-4 py-3 text-left text-xs font-semibold text-neutral-700">
                Control Name
              </th>
              {frameworks.map((fw) => (
                <th
                  key={fw}
                  className="px-4 py-3 text-left text-xs font-semibold text-neutral-700 whitespace-nowrap"
                >
                  {fw}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredMatrix.length === 0 ? (
              <tr>
                <td colSpan={frameworks.length + 1} className="px-4 py-8 text-center text-sm text-neutral-500">
                  No controls match your search
                </td>
              </tr>
            ) : (
              filteredMatrix.map((row, idx) => (
                <tr key={idx} className="border-b border-neutral-100 hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-neutral-900 max-w-xs">
                    {row.control_name}
                  </td>
                  {frameworks.map((fw) => {
                    const status = row[fw] || '—';
                    return (
                      <td key={fw} className="px-4 py-3 text-xs whitespace-nowrap">
                        <span
                          className={`px-2 py-1 rounded border inline-block ${getStatusColor(status)}`}
                        >
                          {status}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 text-xs mt-4 pt-4 border-t border-neutral-200">
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-red-100 border border-red-300" />
          <span className="text-neutral-600">Mandatory/Required</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-yellow-100 border border-yellow-300" />
          <span className="text-neutral-600">Recommended</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded bg-blue-100 border border-blue-300" />
          <span className="text-neutral-600">Optional</span>
        </div>
      </div>

      {/* Summary */}
      {searchTerm && (
        <p className="text-xs text-neutral-500 text-center">
          Showing {filteredMatrix.length} of {matrix.length} controls
        </p>
      )}
    </div>
  );
};
