import { NextRequest, NextResponse } from 'next/server';
import { verifySession } from './lib/session';

const PUBLIC_PATHS = new Set(['/login', '/api/auth/google', '/api/auth/logout']);

export async function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (PUBLIC_PATHS.has(path)) return NextResponse.next();

  const token = request.cookies.get('geomatrix_session')?.value;
  const valid = await verifySession(token);

  if (valid) return NextResponse.next();

  if (path.startsWith('/api/')) {
    return NextResponse.json({ error: 'Authentication required.' }, { status: 401 });
  }

  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('next', path);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/projects/:path*',
    '/map/:path*',
    '/alerts/:path*',
    '/analytics/:path*',
    '/reports/:path*',
    '/data/:path*',
    '/model/:path*',
    '/admin/:path*',
    '/api/:path*',
  ],
};
