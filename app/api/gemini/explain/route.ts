import { NextRequest, NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    if (!BACKEND) {
      return NextResponse.json(
        {
          status: 'error',
          label: 'AI-generated decision support',
          summary: 'Gemini backend is not configured. Set NEXT_PUBLIC_API_URL to the FastAPI service URL.',
          source: 'configuration',
        },
        { status: 503 },
      );
    }

    const upstream = await fetch(`${backendUrl()}/api/gemini/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    const text = await upstream.text();
    let data: unknown = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { error: text || 'Invalid backend response' };
    }

    return NextResponse.json(data, { status: upstream.status });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Gemini proxy error';
    return NextResponse.json(
      { status: 'error', label: 'AI-generated decision support', summary: message, source: 'proxy_error' },
      { status: 502 },
    );
  }
}
