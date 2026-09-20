import { NextResponse } from 'next/server';
import { z } from 'zod';

const schema = z.object({
  name: z.string().trim().min(2).max(120),
  email: z.string().trim().email(),
  password: z.string().min(8).max(128),
});

export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());

  if (!parsed.success) {
    return NextResponse.json(
      { error: 'Enter a valid name, email and password of at least 8 characters.' },
      { status: 400 },
    );
  }

  return NextResponse.json({
    success: true,
    message: 'Demo account registration validated.',
    user: {
      name: parsed.data.name,
      email: parsed.data.email.toLowerCase(),
    },
    storage: 'browser-only',
  });
}
