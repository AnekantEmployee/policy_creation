'use client';

import React, { useState } from 'react';

interface Tab {
  label: string;
  value: string;
  content: React.ReactNode;
  icon?: React.ReactNode;
  badge?: number;
}

interface TabsProps {
  tabs: Tab[];
  defaultValue?: string;
  onChange?: (value: string) => void;
  variant?: 'default' | 'pill';
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  defaultValue,
  onChange,
  variant = 'default',
}) => {
  const [activeTab, setActiveTab] = useState(defaultValue || tabs[0]?.value || '');

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    onChange?.(value);
  };

  const activeTabContent = tabs.find((tab) => tab.value === activeTab)?.content;

  return (
    <div className="w-full">
      {/* Tab List */}
      <div
        className={`flex gap-2 overflow-x-auto ${variant === 'pill' ? 'bg-neutral-100 p-1 rounded-lg' : 'border-b border-neutral-200'}`}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.value;

          return (
            <button
              key={tab.value}
              onClick={() => handleTabChange(tab.value)}
              className={`px-4 py-2.5 font-medium text-sm whitespace-nowrap transition-all duration-200 flex items-center gap-2 ${
                variant === 'pill'
                  ? isActive
                    ? 'bg-white text-primary-600 rounded-md shadow-sm'
                    : 'text-neutral-600 hover:text-neutral-900'
                  : isActive
                    ? 'text-primary-600 border-b-2 border-primary-600'
                    : 'text-neutral-600 border-b-2 border-transparent hover:text-neutral-900'
              }`}
            >
              {tab.icon && <span className="flex-shrink-0">{tab.icon}</span>}
              {tab.label}
              {tab.badge && (
                <span className="ml-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-primary-600 text-xs font-semibold text-white">
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="mt-4 animate-fade-in">{activeTabContent}</div>
    </div>
  );
};
