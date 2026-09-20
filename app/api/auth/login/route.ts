import { NextResponse } from 'next/server';
import { z } from 'zod';
import { createSession } from '../../../../lib/session';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(1).max(256),
});

const DEMO_USERS = [
  { name: 'Demo Administrator', email: 'admin@geomatrix.demo', password: 'GeoMatrix@123', role: 'Administrator' },
  { name: 'Demo Analyst', email: 'analyst@geomatrix.demo', password: 'Analyst@123', role: 'Analyst' },
];

export async function POST(request: Request) {
  try {
    const parsed = schema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json({ error: 'Enter a valid email and password.' }, { status: 400 });
    }

    const email = parsed.data.email.trim().toLowerCase();
    const password = parsed.data.password;

    const configuredEmail = process.env.AUTH_EMAIL?.trim().toLowerCase();
    const configuredPassword = process.env.AUTH_PASSWORD ?? '';

    let identity: { name: string; email: string; role: string } | null = null;

    if (configuredEmail && configuredPassword && email === configuredEmail && password === configuredPassword) {
      identity = {
        name: process.env.AUTH_NAME?.trim() || 'GEOMATRIX Administrator',
        email: configuredEmail,
        role: process.env.AUTH_ROLE?.trim() || 'Administrator',
      };
    } else {
      const demo = DEMO_USERS.find(user => user.email === email && user.password === password);
      if (demo) {
        identity = { name: demo.name, email: demo.email, role: demo.role };
      }
    }

    if (!identity) {
      return NextResponse.json(
        { error: 'Invalid login details. Use one of the demo accounts shown on this page.' },
        { status: 401 },
      );
    }

    const session = await createSession({ email: identity.email, name: identity.name });
    const response = NextResponse.json({
      success: true,
      email: identity.email,
      name: identity.name,
      role: identity.role,
    });

    response.cookies.set('geomatrix_session', session, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      path: '/',
      maxAge: 8 * 60 * 60,
    });

    return response;
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unable to sign in.' },
      { status: 500 },
    );
  }
}
