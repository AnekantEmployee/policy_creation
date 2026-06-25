'use client';

import React from 'react';
import { ChevronLeft, ChevronRight, X } from 'lucide-react';

interface ChatNavigationProps {
  onBack?: () => void;
  onNext?: () => void;
  onExit?: () => void;
  canGoBack?: boolean;
  canGoNext?: boolean;
  backLabel?: string;
  nextLabel?: string;
}

export const ChatNavigation: React.FC<ChatNavigationProps> = ({
  onBack,
  onNext,
  onExit,
  canGoBack = true,
  canGoNext = true,
  backLabel = 'Back',
  nextLabel = 'Next',
}) => {
  return (
    <div className="ml-11 flex gap-2 items-center justify-between">
      <div className="flex gap-2">
        {onBack && (
          <button
            onClick={onBack}
            disabled={!canGoBack}
            className={`px-4 py-2 text-xs font-medium rounded-lg transition-colors flex items-center gap-1 ${
              canGoBack
                ? 'text-neutral-600 border border-neutral-200 hover:bg-neutral-50'
                : 'text-neutral-300 border border-neutral-200 bg-neutral-50 cursor-not-allowed'
            }`}
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            {backLabel}
          </button>
        )}
        {onNext && (
          <button
            onClick={onNext}
            disabled={!canGoNext}
            className={`px-4 py-2 text-xs font-medium rounded-lg transition-colors flex items-center gap-1 ${
              canGoNext
                ? 'text-white bg-gradient-to-r from-primary-600 to-secondary-500 hover:opacity-90'
                : 'text-neutral-400 bg-neutral-200 cursor-not-allowed'
            }`}
          >
            {nextLabel}
            <ChevronRight className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
      {onExit && (
        <button
          onClick={onExit}
          className="px-3 py-2 text-xs font-medium text-neutral-500 hover:text-neutral-700 rounded-lg hover:bg-neutral-100 transition-colors flex items-center gap-1"
          title="Exit to landing page"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      )}
    </div>
  );
};
