const encoder = new TextEncoder();

function encode(value: string): string {
  const bytes = encoder.encode(value);
  let binary = '';
  bytes.forEach(byte => { binary += String.fromCharCode(byte); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function decode(value: string): string {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4);
  const binary = atob(padded);
  return new TextDecoder().decode(Uint8Array.from(binary, char => char.charCodeAt(0)));
}

async function signature(value: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  const digest = await crypto.subtle.sign('HMAC', key, encoder.encode(value));
  return encode(String.fromCharCode(...new Uint8Array(digest)));
}

export async function createSession(payload: { email: string; name: string }): Promise<string> {
  const secret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET;
  if (!secret) throw new Error('AUTH_SECRET is not configured.');
  const body = encode(JSON.stringify({ ...payload, iat: Date.now() }));
  return `${body}.${await signature(body, secret)}`;
}

export async function verifySession(token: string | undefined): Promise<boolean> {
  const secret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET;
  if (!secret || !token) return false;
  const [body, sig] = token.split('.');
  if (!body || !sig) return false;
  try {
    const expected = await signature(body, secret);
    if (expected !== sig) return false;
    const parsed = JSON.parse(decode(body)) as { iat?: number };
    return typeof parsed.iat === 'number' && Date.now() - parsed.iat < 8 * 60 * 60 * 1000;
  } catch {
    return false;
  }
}
