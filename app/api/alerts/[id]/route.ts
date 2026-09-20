import { NextRequest, NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const { id } = await params;
    const body = await req.json();
    const response = await fetch(`${backendUrl()}/api/alerts/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const text = await response.text();
    let data: unknown = {};
    try { data = text ? JSON.parse(text) : {}; } catch { data = { error: text }; }
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Alert update failed.' }, { status: 503 });
  }
}
