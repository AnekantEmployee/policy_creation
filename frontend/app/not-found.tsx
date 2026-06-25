import React from 'react';
import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col items-center justify-center gap-4 text-center px-6">
      <span className="text-6xl">🔍</span>
      <h2 className="text-2xl font-bold text-neutral-900">Page not found</h2>
      <p className="text-neutral-500">This page doesn't exist.</p>
      <Link
        href="/"
        className="mt-2 px-4 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
      >
        ← Back to Wizard
      </Link>
    </div>
  );
}
