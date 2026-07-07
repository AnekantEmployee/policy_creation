import type { Metadata } from 'next';
import { Toaster } from 'react-hot-toast';
import { ConditionalLayout } from './components/ConditionalLayout';
import './globals.css';

export const metadata: Metadata = {
  title: 'ComplianceIQ — AI Policy Generator',
  description: 'AI-powered GRC policy and procedure generation',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased" suppressHydrationWarning>
        <ConditionalLayout>{children}</ConditionalLayout>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#111827',
              borderRadius: '0.75rem',
              border: '1px solid #e5e7eb',
              boxShadow: '0 10px 15px -3px rgba(0,0,0,0.08)',
              fontSize: '0.875rem',
            },
            success: { style: { background: '#f0fdf4', color: '#166534', border: '1px solid #86efac' }, iconTheme: { primary: '#16a34a', secondary: '#fff' } },
            error:   { style: { background: '#fef2f2', color: '#991b1b', border: '1px solid #fecaca' }, iconTheme: { primary: '#dc2626', secondary: '#fff' } },
          }}
        />
      </body>
    </html>
  );
}
