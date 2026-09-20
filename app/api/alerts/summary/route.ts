import { NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

export async function GET() {
  try {
    const res = await fetch(`${backendUrl()}/api/alerts/summary`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (err) {
    return NextResponse.json({ total: 0, open: 0, critical: 0, high: 0 }, { status: 200 });
  }
}
