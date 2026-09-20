import { NextResponse } from 'next/server';
import { z } from 'zod';
import { createSession } from '../../../../lib/session';

const requestSchema = z.object({ credential: z.string().min(1) });

export async function POST(request: Request) {
  try {
    const parsed = requestSchema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json({ error: 'Google credential is required.' }, { status: 400 });
    }

    const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID?.trim();
    if (!clientId) {
      return NextResponse.json({ error: 'Google sign-in is not configured.' }, { status: 503 });
    }

    const tokenResponse = await fetch(
      `https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(parsed.data.credential)}`,
      { cache: 'no-store' },
    );
    if (!tokenResponse.ok) {
      return NextResponse.json({ error: 'Google credential could not be verified.' }, { status: 401 });
    }

    const token = await tokenResponse.json() as {
      aud?: string;
      email?: string;
      email_verified?: string;
      name?: string;
    };

    if (
      token.aud !== clientId ||
      token.email_verified !== 'true' ||
      !token.email ||
      !token.name
    ) {
      return NextResponse.json({ error: 'Google account verification failed.' }, { status: 401 });
    }

    const session = await createSession({ email: token.email, name: token.name });
    const response = NextResponse.json({ email: token.email, name: token.name });
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
      { error: error instanceof Error ? error.message : 'Authentication failed.' },
      { status: 500 },
    );
  }
}
