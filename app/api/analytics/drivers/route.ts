import { NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

export async function GET() {
  try {
    const response = await fetch(`${backendUrl()}/api/analytics/drivers`, { cache: 'no-store' });
    const text = await response.text();
    let data: unknown = [];
    try { data = text ? JSON.parse(text) : []; } catch { data = []; }
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Driver analytics unavailable.' }, { status: 503 });
  }
}
