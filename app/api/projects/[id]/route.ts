import { NextRequest, NextResponse } from 'next/server';

function backendUrl(): string {
  const url = (process.env.MODEL_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? '').trim();
  if (!url) throw new Error('Backend API is not configured. Set MODEL_API_URL.');
  return url.replace(/\/+$/, '');
}

async function readJsonPayload(res: Response) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function GET(_: NextRequest, context: { params: Promise<{ id: string }> | { id: string } }) {
  try {
    const resolvedParams = context.params instanceof Promise ? await context.params : context.params;
    const id = resolvedParams?.id;
    if (!id) {
      return NextResponse.json({ error: 'Missing project ID' }, { status: 400 });
    }

    const upstream = await fetch(`${backendUrl()}/api/projects/${encodeURIComponent(id)}`, {
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });
    const payload = await readJsonPayload(upstream);

    if (!upstream.ok) {
      return NextResponse.json(
        typeof payload === 'object' && payload ? payload : { error: 'Project not found.' },
        { status: upstream.status }
      );
    }

    return NextResponse.json(payload ?? {}, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json({ error: `Failed to fetch project: ${err.message}` }, { status: 500 });
  }
}

export async function PATCH(req: NextRequest, context: { params: Promise<{ id: string }> | { id: string } }) {
  try {
    const resolvedParams = context.params instanceof Promise ? await context.params : context.params;
    const id = resolvedParams?.id;
    const body = await req.json().catch(() => ({}));
    const upstream = await fetch(`${backendUrl()}/api/projects/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const payload = await readJsonPayload(upstream);

    if (!upstream.ok) {
      return NextResponse.json(
        typeof payload === 'object' && payload ? payload : { error: 'Project update failed.' },
        { status: upstream.status }
      );
    }

    return NextResponse.json(payload ?? {}, { status: upstream.status });
  } catch (err: any) {
    return NextResponse.json({ error: `Update failed: ${err.message}` }, { status: 500 });
  }
}

export async function DELETE(_: NextRequest, context: { params: Promise<{ id: string }> | { id: string } }) {
  try {
    const resolvedParams = context.params instanceof Promise ? await context.params : context.params;
    const id = resolvedParams?.id;
    const upstream = await fetch(`${backendUrl()}/api/projects/${encodeURIComponent(id)}`, { method: 'DELETE' });

    if (!upstream.ok) {
      const payload = await readJsonPayload(upstream);
      return NextResponse.json(
        typeof payload === 'object' && payload ? payload : { error: 'Project deletion failed.' },
        { status: upstream.status }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (err: any) {
    return NextResponse.json({ error: `Deletion failed: ${err.message}` }, { status: 500 });
  }
}
