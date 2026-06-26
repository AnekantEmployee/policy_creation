'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useWizardStore } from '@/store/wizardStore';
import { BotBubble, UserBubble, ChatGroup } from './ChatBubble';
import { ArrowRight, X } from 'lucide-react';

const EXAMPLES = [
  'Indian healthcare SaaS startup',
  'Indian Information Technology services',
  'US fintech payment processor',
  'EU ecommerce retail company',
  'Global manufacturing enterprise',
];

interface Props { active: boolean; done: boolean; }

export const ChatOrgInfo: React.FC<Props> = ({ active, done }) => {
  const router = useRouter();
  const { orgName, orgDescription, orgWebsite, orgCountry, setOrgInfo, setPhase, reset } = useWizardStore();

  // Pre-fill form with whatever is already in the store (covers the "back" case)
  const [form, setForm] = useState({
    name:        orgName        ?? '',
    description: orgDescription ?? '',
    website:     orgWebsite     ?? '',
    country:     orgCountry     ?? '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.name.trim())        errs.name        = 'Required';
    if (!form.description.trim()) errs.description = 'Required';
    if (!form.country.trim())     errs.country     = 'Required';
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setOrgInfo({
      orgName:        form.name.trim(),
      orgDescription: form.description.trim(),
      orgWebsite:     form.website.trim(),
      orgCountry:     form.country.trim(),
    });
    setPhase('analyzing');
  };

  const handleExit = () => {
    reset();
    router.push('/');
  };

  if (done) {
    return (
      <ChatGroup>
        <BotBubble done>Tell us about your organization.</BotBubble>
        <UserBubble>
          <div className="space-y-0.5">
            <p className="font-semibold">{orgName}</p>
            <p className="opacity-80 text-xs">{orgDescription} · {orgCountry}</p>
          </div>
        </UserBubble>
      </ChatGroup>
    );
  }

  return (
    <ChatGroup>
      <BotBubble>
        <div className="space-y-1">
          <p className="font-semibold text-base">👋 Welcome to ComplianceIQ</p>
          <p>Let's create tailored compliance policies and procedures for your organization. First, tell me about your company.</p>
        </div>
      </BotBubble>

      {active && (
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-neutral-200 shadow-sm p-5 space-y-4 ml-11">
          {/* Org name */}
          <div>
            <label className="block text-xs font-semibold text-neutral-600 mb-1.5 uppercase tracking-wide">Organization Name *</label>
            <input
              value={form.name}
              onChange={(e) => { setForm(p => ({ ...p, name: e.target.value })); setErrors(p => ({ ...p, name: '' })); }}
              placeholder="e.g. Acme Corporation"
              className={`w-full px-3 py-2 text-sm rounded-lg border-2 bg-neutral-50 focus:bg-white focus:outline-none transition-colors ${errors.name ? 'border-red-400' : 'border-neutral-200 focus:border-primary-500'}`}
            />
            {errors.name && <p className="text-xs text-red-500 mt-1">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-neutral-600 mb-1.5 uppercase tracking-wide">About Your Organization *</label>
            <input
              value={form.description}
              onChange={(e) => { setForm(p => ({ ...p, description: e.target.value })); setErrors(p => ({ ...p, description: '' })); }}
              placeholder="e.g. Indian healthcare SaaS startup"
              className={`w-full px-3 py-2 text-sm rounded-lg border-2 bg-neutral-50 focus:bg-white focus:outline-none transition-colors ${errors.description ? 'border-red-400' : 'border-neutral-200 focus:border-primary-500'}`}
            />
            {errors.description && <p className="text-xs text-red-500 mt-1">{errors.description}</p>}
            <p className="text-xs text-neutral-400 mt-1">Include industry, size, and focus area</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {EXAMPLES.map(ex => (
                <button key={ex} type="button" onClick={() => setForm(p => ({ ...p, description: ex }))}
                  className="px-2.5 py-1 text-xs rounded-full bg-primary-50 text-primary-700 border border-primary-200 hover:bg-primary-100 transition-colors">
                  {ex}
                </button>
              ))}
            </div>
          </div>

          {/* Country + Website */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-neutral-600 mb-1.5 uppercase tracking-wide">Country *</label>
              <input
                value={form.country}
                onChange={(e) => { setForm(p => ({ ...p, country: e.target.value })); setErrors(p => ({ ...p, country: '' })); }}
                placeholder="e.g. India, USA, Germany"
                className={`w-full px-3 py-2 text-sm rounded-lg border-2 bg-neutral-50 focus:bg-white focus:outline-none transition-colors ${errors.country ? 'border-red-400' : 'border-neutral-200 focus:border-primary-500'}`}
              />
              {errors.country && <p className="text-xs text-red-500 mt-1">{errors.country}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold text-neutral-600 mb-1.5 uppercase tracking-wide">Website <span className="font-normal normal-case text-neutral-400">(optional)</span></label>
              <input
                value={form.website}
                onChange={(e) => setForm(p => ({ ...p, website: e.target.value }))}
                placeholder="https://example.com"
                className="w-full px-3 py-2 text-sm rounded-lg border-2 border-neutral-200 bg-neutral-50 focus:bg-white focus:outline-none focus:border-primary-500 transition-colors"
              />
            </div>
          </div>

          <button type="submit"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 transition-opacity shadow-sm">
            Start Analysis <ArrowRight className="h-4 w-4" />
          </button>

          {/* Exit Button */}
          <button type="button" onClick={handleExit}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-neutral-100 text-neutral-700 text-sm font-semibold rounded-xl hover:bg-neutral-200 transition-colors">
            <X className="h-4 w-4" /> Exit to Landing
          </button>
        </form>
      )}
    </ChatGroup>
  );
};
