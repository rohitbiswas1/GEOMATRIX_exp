import { NextRequest, NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

export async function POST(_: NextRequest, context: { params: Promise<{ id: string }> | { id: string } }) {
  try {
    const resolvedParams = context.params instanceof Promise ? await context.params : context.params;
    const id = resolvedParams?.id;
    const upstream = await fetch(`${backendUrl()}/api/projects/${encodeURIComponent(id)}/predict-risk`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
    });
    const text = await upstream.text();
    const data = text ? JSON.parse(text) : {};
    return NextResponse.json(data, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json({ error: `Prediction failed: ${err.message}` }, { status: 500 });
  }
}
