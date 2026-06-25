import { NextRequest, NextResponse } from 'next/server';

/**
 * Proxy (Next.js 16+ equivalent of middleware).
 * Enforces authentication and role-based access before pages render,
 * eliminating the flash-of-unauthenticated-content that client-side
 * useEffect guards cause.
 *
 * Token storage: the auth store writes `access_token` as a cookie on
 * login so this file can read it without a DB round-trip.
 */

// Routes that require no authentication
const PUBLIC_ROUTES = ['/auth'];

// Routes restricted to admin role only
const ADMIN_ROUTES = ['/admin'];

// Routes restricted to roles that can generate/modify content
const WRITE_ONLY_ROUTES = ['/wizard'];
const WRITE_ROLES = ['admin', 'compliance_officer'];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Always allow public routes through
  if (PUBLIC_ROUTES.some(route => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Read the access token from the cookie set by authStore on login
  const token = request.cookies.get('access_token')?.value;

  // No token → send to /auth, preserving the intended destination
  if (!token) {
    const authUrl = new URL('/auth', request.url);
    if (pathname !== '/') {
      authUrl.searchParams.set('redirect', pathname);
    }
    return NextResponse.redirect(authUrl);
  }

  // Decode JWT payload (no signature check — that's the backend's job;
  // we only need the role claim for routing decisions).
  let role: string | null = null;
  try {
    const payloadBase64 = token.split('.')[1];
    if (payloadBase64) {
      const decoded = JSON.parse(
        Buffer.from(payloadBase64, 'base64url').toString('utf-8')
      );
      role = decoded.role ?? null;
    }
  } catch {
    // Malformed token — force re-login
    const authUrl = new URL('/auth', request.url);
    return NextResponse.redirect(authUrl);
  }

  // Admin-only routes — non-admins go back to home
  if (ADMIN_ROUTES.some(r => pathname.startsWith(r))) {
    if (role !== 'admin') {
      return NextResponse.redirect(new URL('/', request.url));
    }
  }

  // Write-only routes (wizard / new scan) — read-only roles go to history
  if (WRITE_ONLY_ROUTES.some(r => pathname.startsWith(r))) {
    if (role && !WRITE_ROLES.includes(role)) {
      return NextResponse.redirect(new URL('/history', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Run on every route except Next.js internals and static files
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};
