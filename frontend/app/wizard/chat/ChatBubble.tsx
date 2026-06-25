'use client';

import React from 'react';

interface BotBubbleProps {
  children: React.ReactNode;
  done?: boolean;
}

export const BotBubble: React.FC<BotBubbleProps> = ({ children, done }) => (
  <div className="flex items-start gap-3">
    <div className={`h-8 w-8 rounded-xl flex items-center justify-center text-sm shrink-0 mt-0.5 shadow-sm ${
      done ? 'bg-green-100 text-green-600' : 'bg-gradient-to-br from-primary-600 to-secondary-500 text-white'
    }`}>
      {done ? '✓' : '⚡'}
    </div>
    <div className="bg-white rounded-2xl rounded-tl-sm border border-neutral-200 px-4 py-3 shadow-sm max-w-xl text-sm text-neutral-800 leading-relaxed">
      {children}
    </div>
  </div>
);

interface UserBubbleProps {
  children: React.ReactNode;
}

export const UserBubble: React.FC<UserBubbleProps> = ({ children }) => (
  <div className="flex justify-end">
    <div className="bg-gradient-to-br from-primary-600 to-secondary-500 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm max-w-xs text-sm leading-relaxed">
      {children}
    </div>
  </div>
);

export const ChatGroup: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="space-y-3">{children}</div>
);
