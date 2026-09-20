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

    const email = parsed.data.email.trim().toLowerCase();
    const name = parsed.data.name.trim();
    const role = parsed.data.role?.trim() || 'User';

    const session = await createSession({ email, name });

    const response = NextResponse.json({
      success: true,
      email,
      name,
      role,
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
      { error: error instanceof Error ? error.message : 'Unable to create the login session.' },
      { status: 500 },
    );
  }
}
