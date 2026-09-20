import { NextResponse } from 'next/server';
import { z } from 'zod';
import { createSession } from '../../../../lib/session';

const schema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(120),
  role: z.string().min(1).max(80).optional(),
});

export async function POST(request: Request) {
  try {
    const parsed = schema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json({ error: 'Valid name and email are required.' }, { status: 400 });
    }

    const session = await createSession({
      email: parsed.data.email.toLowerCase(),
      name: parsed.data.name,
    });

    const response = NextResponse.json({
      success: true,
      email: parsed.data.email.toLowerCase(),
      name: parsed.data.name,
      role: parsed.data.role ?? 'User',
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
      { error: error instanceof Error ? error.message : 'Session creation failed.' },
      { status: 500 },
    );
  }
}
