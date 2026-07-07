'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardBody } from '../components/Card';
import {
  AlertCircle, Eye, EyeOff, Mail, Lock, User, CheckCircle, Clock,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import toast from 'react-hot-toast';

type Tab = 'signin' | 'signup';

// ─── Shared small UI helpers ────────────────────────────────────────────────

function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-gradient-to-br from-neutral-900 via-primary-950 to-neutral-900 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white text-xl shadow-lg">
              ⚡
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white">ComplianceIQ</h1>
          <p className="text-sm text-neutral-400">AI-powered GRC policy generation</p>
        </div>
        {children}
      </div>
    </main>
  );
}

function Field({
  label, error, children,
}: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-neutral-600 mb-1.5 uppercase tracking-wide">
        {label}
      </label>
      {children}
      {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
    </div>
  );
}

function FieldInput({
  icon, error, suffix, children,
}: {
  icon: React.ReactNode;
  error?: boolean;
  suffix?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex items-center rounded-lg border-2 bg-neutral-50 focus-within:bg-white transition-colors ${
      error ? 'border-red-400' : 'border-neutral-200 focus-within:border-primary-500'
    }`}>
      {/* suppressHydrationWarning prevents noise from browser extensions (e.g. Dark Reader)
          injecting attributes onto SVG elements inside these spans */}
      <span className="pl-3 text-neutral-400 shrink-0" suppressHydrationWarning>{icon}</span>
      <div className="flex-1 [&_input]:w-full [&_input]:px-2 [&_input]:py-2 [&_input]:text-sm [&_input]:bg-transparent [&_input]:outline-none">
        {children}
      </div>
      {suffix && <span className="pr-2 shrink-0" suppressHydrationWarning>{suffix}</span>}
    </div>
  );
}

// ─── Pending approval screen ────────────────────────────────────────────────

function PendingApproval({ email, onBack }: { email: string; onBack: () => void }) {
  return (
    <AuthShell>
      <Card>
        <CardBody className="p-8 text-center space-y-5">
          <div className="flex justify-center">
            <div className="h-14 w-14 rounded-full bg-amber-100 flex items-center justify-center" suppressHydrationWarning>
              <Clock className="h-7 w-7 text-amber-600" />
            </div>
          </div>
          <div>
            <h2 className="text-lg font-bold text-neutral-900 mb-1">Pending Approval</h2>
            <p className="text-sm text-neutral-600">
              Your account for <strong>{email}</strong> has been created and is awaiting admin
              approval. You can sign in once an administrator approves your request.
            </p>
          </div>
          <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-700 text-left space-y-1">
            <p className="font-semibold">What happens next?</p>
            <p>1. An admin will review your registration.</p>
            <p>2. Once approved, sign in with your credentials.</p>
            <p>3. Contact your administrator for expedited access.</p>
          </div>
          <button
            onClick={onBack}
            className="w-full py-2 text-sm font-semibold rounded-lg bg-neutral-100 text-neutral-700 hover:bg-neutral-200 transition-colors"
          >
            Back to Sign In
          </button>
        </CardBody>
      </Card>
    </AuthShell>
  );
}

// ─── Main auth form (uses useSearchParams — must be inside Suspense) ────────

function AuthPageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  // Only allow redirect to known safe internal paths — never a stale or external value
  const rawRedirect = searchParams.get('redirect') || '/';
  const redirectTo = rawRedirect.startsWith('/') && !rawRedirect.startsWith('//') ? rawRedirect : '/';

  const { login, signup, isAuthenticated, initializeFromStorage } = useAuthStore();

  const [tab, setTab] = useState<Tab>('signin');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [pendingEmail, setPendingEmail] = useState<string | null>(null);

  const [signinForm, setSigninForm] = useState({ email: '', password: '' });
  const [signupForm, setSignupForm] = useState({
    fullName: '', email: '', username: '', password: '', confirmPassword: '',
  });

  useEffect(() => { initializeFromStorage(); }, [initializeFromStorage]);
  useEffect(() => {
    if (isAuthenticated) router.replace(redirectTo);
  }, [isAuthenticated, redirectTo, router]);

  const switchTab = (t: Tab) => { setTab(t); setErrors({}); setPendingEmail(null); };

  // ── Sign In ──────────────────────────────────────────────────────────────

  const handleSignin = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!signinForm.email)    errs.email    = 'Email is required';
    if (!signinForm.password) errs.password = 'Password is required';
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    setErrors({});
    try {
      await login(signinForm.email, signinForm.password);
      toast.success('Welcome back!');
      router.replace(redirectTo);
    } catch (err: any) {
      const msg: string = err?.message || 'Login failed';
      if (msg.toLowerCase().includes('pending') || msg.includes('403')) {
        setErrors({ form: 'Your account is pending admin approval. Please wait.' });
      } else {
        setErrors({ form: msg });
      }
    } finally {
      setLoading(false);
    }
  };

  // ── Sign Up ──────────────────────────────────────────────────────────────

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs: Record<string, string> = {};
    if (!signupForm.email) errs.email = 'Email is required';
    if (!signupForm.username || signupForm.username.length < 3)
      errs.username = 'Username must be at least 3 characters';
    if (!signupForm.password || signupForm.password.length < 8)
      errs.password = 'Password must be at least 8 characters';
    if (signupForm.password !== signupForm.confirmPassword)
      errs.confirmPassword = 'Passwords do not match';
    if (Object.keys(errs).length) { setErrors(errs); return; }

    setLoading(true);
    setErrors({});
    try {
      await signup(
        signupForm.email,
        signupForm.username,
        signupForm.password,
        signupForm.fullName || undefined,
      );
      setPendingEmail(signupForm.email);
      toast.success('Account created — awaiting admin approval.');
    } catch (err: any) {
      setErrors({ form: err?.message || 'Signup failed' });
    } finally {
      setLoading(false);
    }
  };

  // ── Pending approval screen ──────────────────────────────────────────────

  if (pendingEmail) {
    return (
      <PendingApproval
        email={pendingEmail}
        onBack={() => { setPendingEmail(null); switchTab('signin'); }}
      />
    );
  }

  // ── Auth card ────────────────────────────────────────────────────────────

  return (
    <AuthShell>
      <Card>
        <CardBody className="p-6 space-y-5">

          {/* Tabs */}
          <div className="flex border-b border-neutral-200">
            {(['signin', 'signup'] as Tab[]).map((t) => (
              <button
                key={t}
                onClick={() => switchTab(t)}
                className={`flex-1 py-3 text-sm font-semibold transition-colors ${
                  tab === t
                    ? 'text-primary-600 border-b-2 border-primary-600'
                    : 'text-neutral-400 hover:text-neutral-600'
                }`}
              >
                {t === 'signin' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          {/* Form-level error */}
          {errors.form && (
            <div className="flex gap-3 p-3 rounded-lg bg-red-50 border border-red-200" suppressHydrationWarning>
              <AlertCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{errors.form}</p>
            </div>
          )}

          {/* ── Sign In form ─────────────────────────────────────────────── */}
          {tab === 'signin' && (
            <form onSubmit={handleSignin} className="space-y-4">
              <Field label="Email Address" error={errors.email}>
                <FieldInput icon={<Mail className="h-4 w-4" />} error={!!errors.email}>
                  <input
                    type="email"
                    value={signinForm.email}
                    autoComplete="email"
                    placeholder="you@example.com"
                    onChange={(e) => {
                      setSigninForm({ ...signinForm, email: e.target.value });
                      setErrors({ ...errors, email: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <Field label="Password" error={errors.password}>
                <FieldInput
                  icon={<Lock className="h-4 w-4" />}
                  error={!!errors.password}
                  suffix={
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="text-neutral-400 hover:text-neutral-600 p-1">
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                >
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={signinForm.password}
                    autoComplete="current-password"
                    placeholder="••••••••"
                    onChange={(e) => {
                      setSigninForm({ ...signinForm, password: e.target.value });
                      setErrors({ ...errors, password: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <button type="submit" disabled={loading}
                className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 disabled:opacity-50 transition-opacity shadow-sm">
                {loading ? 'Signing in…' : 'Sign In'}
              </button>

              <p className="text-xs text-center text-neutral-400">
                Demo — <span className="font-mono">demo@example.com</span>{' '}
                / <span className="font-mono">Demo1234!</span>
              </p>
            </form>
          )}

          {/* ── Sign Up form ─────────────────────────────────────────────── */}
          {tab === 'signup' && (
            <form onSubmit={handleSignup} className="space-y-4">
              <Field label="Full Name">
                <FieldInput icon={<User className="h-4 w-4" />}>
                  <input
                    type="text"
                    value={signupForm.fullName}
                    autoComplete="name"
                    placeholder="Jane Smith"
                    onChange={(e) => setSignupForm({ ...signupForm, fullName: e.target.value })}
                  />
                </FieldInput>
              </Field>

              <Field label="Email Address" error={errors.email}>
                <FieldInput icon={<Mail className="h-4 w-4" />} error={!!errors.email}>
                  <input
                    type="email"
                    value={signupForm.email}
                    autoComplete="email"
                    placeholder="you@example.com"
                    onChange={(e) => {
                      setSignupForm({ ...signupForm, email: e.target.value });
                      setErrors({ ...errors, email: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <Field label="Username" error={errors.username}>
                <FieldInput icon={<User className="h-4 w-4" />} error={!!errors.username}>
                  <input
                    type="text"
                    value={signupForm.username}
                    autoComplete="username"
                    placeholder="janesmith"
                    onChange={(e) => {
                      setSignupForm({ ...signupForm, username: e.target.value });
                      setErrors({ ...errors, username: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <Field label="Password" error={errors.password}>
                <FieldInput
                  icon={<Lock className="h-4 w-4" />}
                  error={!!errors.password}
                  suffix={
                    <button type="button" onClick={() => setShowPassword(!showPassword)}
                      className="text-neutral-400 hover:text-neutral-600 p-1">
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  }
                >
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={signupForm.password}
                    autoComplete="new-password"
                    placeholder="Min. 8 characters"
                    onChange={(e) => {
                      setSignupForm({ ...signupForm, password: e.target.value });
                      setErrors({ ...errors, password: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <Field label="Confirm Password" error={errors.confirmPassword}>
                <FieldInput icon={<Lock className="h-4 w-4" />} error={!!errors.confirmPassword}>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={signupForm.confirmPassword}
                    autoComplete="new-password"
                    placeholder="Re-enter password"
                    onChange={(e) => {
                      setSignupForm({ ...signupForm, confirmPassword: e.target.value });
                      setErrors({ ...errors, confirmPassword: '' });
                    }}
                  />
                </FieldInput>
              </Field>

              <div className="flex gap-2 p-3 rounded-lg bg-blue-50 border border-blue-200" suppressHydrationWarning>
                <CheckCircle className="h-4 w-4 text-blue-500 shrink-0 mt-0.5" />
                <p className="text-xs text-blue-700">
                  New accounts require admin approval before you can sign in.
                </p>
              </div>

              <button type="submit" disabled={loading}
                className="w-full py-2.5 bg-gradient-to-r from-primary-600 to-secondary-500 text-white text-sm font-semibold rounded-xl hover:opacity-90 disabled:opacity-50 transition-opacity shadow-sm">
                {loading ? 'Submitting…' : 'Request Access'}
              </button>
            </form>
          )}

        </CardBody>
      </Card>
    </AuthShell>
  );
}

// ─── Default export — wraps inner component in Suspense ─────────────────────

export default function AuthPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-gradient-to-br from-neutral-900 via-primary-950 to-neutral-900 flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
      </main>
    }>
      <AuthPageInner />
    </Suspense>
  );
}
