'use client';

import React, { useState } from 'react';
import { useWizardStore } from '@/store/wizardStore';
import { Button } from '@/app/components/Button';
import { Input } from '@/app/components/Input';
import { ArrowRight, Building2 } from 'lucide-react';

const EXAMPLE_DESCRIPTIONS = [
  'Indian healthcare SaaS startup',
  'Indian Information Technology services',
  'US fintech payment processor',
  'EU ecommerce retail company',
  'Global manufacturing enterprise',
];

export const StepOrgInfo: React.FC = () => {
  const { setOrgInfo, setPhase } = useWizardStore();
  const [form, setForm] = useState({ name: '', description: '', website: '', country: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setForm((p) => ({ ...p, [name]: value }));
    if (errors[name]) setErrors((p) => ({ ...p, [name]: '' }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!form.name.trim())        errs.name        = 'Organization name is required';
    if (!form.description.trim()) errs.description = 'Brief description is required';
    if (!form.country.trim())     errs.country     = 'Country is required';
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setOrgInfo({
      orgName:        form.name.trim(),
      orgDescription: form.description.trim(),
      orgWebsite:     form.website.trim(),
      orgCountry:     form.country.trim(),
    });
    setPhase('analyzing');
  };

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="text-center space-y-3">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-gradient-to-br from-primary-600 to-secondary-500 flex items-center justify-center text-white text-3xl shadow-lg">
          🛡️
        </div>
        <h2 className="text-2xl font-bold text-neutral-900">Tell us about your organization</h2>
        <p className="text-neutral-500">We'll use AI to analyze your compliance requirements and recommend the right frameworks.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 bg-white rounded-2xl border border-neutral-200 shadow-sm p-6">
        <Input
          label="Organization Name *"
          name="name"
          placeholder="e.g. Acme Corporation"
          value={form.name}
          onChange={handleChange}
          error={errors.name}
        />

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-1.5">
            Brief Description *
            <span className="ml-1 text-neutral-400 font-normal">(industry, region, type)</span>
          </label>
          <Input
            name="description"
            placeholder="e.g. Indian healthcare SaaS startup"
            value={form.description}
            onChange={handleChange}
            error={errors.description}
          />
          <div className="flex flex-wrap gap-2 mt-2">
            {EXAMPLE_DESCRIPTIONS.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setForm((p) => ({ ...p, description: ex }))}
                className="px-2.5 py-1 text-xs rounded-full bg-primary-50 text-primary-700 border border-primary-200 hover:bg-primary-100 transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Country / Region *"
            name="country"
            placeholder="e.g. India, USA, Germany"
            value={form.country}
            onChange={handleChange}
            error={errors.country}
          />
          <Input
            label="Website"
            name="website"
            placeholder="https://example.com (optional)"
            value={form.website}
            onChange={handleChange}
            helperText="Enables deeper AI analysis"
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          fullWidth
          size="lg"
          icon={<ArrowRight className="h-5 w-5" />}
          iconPosition="right"
        >
          Analyze My Organization
        </Button>
      </form>
    </div>
  );
};
