"use client";

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, Lock, Mail, Map, User, UserPlus } from 'lucide-react';

type DemoUser = { name: string; email: string; password: string };

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [done, setDone] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setDone('');

    const trimmedName = name.trim();
    const normalizedEmail = email.trim().toLowerCase();

    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmedName, email: normalizedEmail, password }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.error || 'Registration failed.');

      const existing = JSON.parse(
        window.localStorage.getItem('geomatrix-demo-users') || '[]'
      ) as DemoUser[];

      const withoutDuplicate = existing.filter(
        user => user.email.toLowerCase() !== normalizedEmail
      );

      localStorage.setItem(
        'geomatrix-demo-users',
        JSON.stringify([
          ...withoutDuplicate,
          { name: trimmedName, email: normalizedEmail, password },
        ])
      );

      setDone('Demo account created successfully. Redirecting to sign in...');
      window.setTimeout(() => router.push('/login'), 700);
    } catch (registrationError) {
      setError(
        registrationError instanceof Error
          ? registrationError.message
          : 'Registration failed.'
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="register-page">
      <div className="register-card">
        <a href="/login" className="back-link">
          <ArrowLeft size={14} /> Back to sign in
        </a>

        <div className="brand">
          <div className="brand-icon"><Map size={20} /></div>
          <div>
            <div className="brand-title">GEOMATRIX</div>
            <div className="brand-sub">LAND ACQUISITION AI</div>
          </div>
        </div>

        <h1>Create demo account</h1>
        <p className="subtitle">
          Create a local demo user for testing the dashboard and login flow.
        </p>

        <form onSubmit={submit}>
          <label className="field">
            <span>Full name</span>
            <div className="input-wrap">
              <User size={16} />
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                required
                minLength={2}
                placeholder="Your name"
                autoComplete="name"
              />
            </div>
          </label>

          <label className="field">
            <span>Email</span>
            <div className="input-wrap">
              <Mail size={16} />
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>
          </label>

          <label className="field">
            <span>Password</span>
            <div className="input-wrap">
              <Lock size={16} />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="At least 8 characters"
                autoComplete="new-password"
              />
            </div>
          </label>

          <label className="field">
            <span>Confirm password</span>
            <div className="input-wrap">
              <Lock size={16} />
              <input
                type="password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
                minLength={8}
                placeholder="Repeat password"
                autoComplete="new-password"
              />
            </div>
          </label>

          {error && <div className="message error" role="alert">{error}</div>}
          {done && <div className="message success">{done}</div>}

          <button type="submit" disabled={loading} className="submit">
            {loading
              ? <><Loader2 size={16} className="spin" /> Creating...</>
              : <><UserPlus size={16} /> Create demo account</>}
          </button>
        </form>

        <div className="note">
          Demo users are stored in this browser only. For a quick test,
          the login page also provides predefined Administrator and Analyst accounts.
        </div>
      </div>

      <style>{\`
        .register-page {
          min-height: 100vh;
          display: grid;
          place-items: center;
          padding: 24px;
          background:
            radial-gradient(circle at 50% 20%, rgba(37,99,235,.18), transparent 45%),
            #06172d;
          color: #f8fafc;
          font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }
        .register-card {
          width: min(480px, 100%);
          padding: 30px;
          border: 1px solid rgba(255,255,255,.14);
          border-radius: 20px;
          background: rgba(11,27,49,.92);
          box-shadow: 0 24px 60px rgba(0,0,0,.35);
        }
        .back-link {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          color: #94a3b8;
          text-decoration: none;
          font-size: 12px;
          margin-bottom: 18px;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 18px;
        }
        .brand-icon {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          display: grid;
          place-items: center;
          background: rgba(37,99,235,.25);
          color: #60a5fa;
        }
        .brand-title {
          font-weight: 800;
          letter-spacing: .08em;
        }
        .brand-sub {
          font-size: 10px;
          color: #93c5fd;
          letter-spacing: .08em;
        }
        h1 {
          margin: 0 0 6px;
          font-size: 24px;
        }
        .subtitle {
          color: #94a3b8;
          font-size: 12px;
          line-height: 1.6;
          margin: 0 0 22px;
        }
        .field {
          display: grid;
          gap: 7px;
          margin-bottom: 14px;
          font-size: 12px;
          color: #e2e8f0;
        }
        .input-wrap {
          position: relative;
          display: flex;
          align-items: center;
        }
        .input-wrap svg {
          position: absolute;
          left: 13px;
          color: #94a3b8;
        }
        input {
          width: 100%;
          height: 44px;
          box-sizing: border-box;
          padding: 0 14px 0 40px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,.14);
          background: rgba(15,23,42,.75);
          color: #f8fafc;
          font-size: 13px;
        }
        input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59,130,246,.2);
        }
        .submit {
          width: 100%;
          height: 46px;
          border: 0;
          border-radius: 10px;
          background: linear-gradient(135deg,#1d4ed8,#2563eb);
          color: #fff;
          font-weight: 700;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          margin-top: 4px;
        }
        .submit:disabled { opacity: .65; cursor: not-allowed; }
        .message {
          padding: 10px 12px;
          border-radius: 10px;
          margin-bottom: 14px;
          font-size: 12px;
        }
        .error {
          border: 1px solid rgba(248,113,113,.3);
          color: #fca5a5;
          background: rgba(239,68,68,.08);
        }
        .success {
          border: 1px solid rgba(52,211,153,.3);
          color: #6ee7b7;
          background: rgba(16,185,129,.08);
        }
        .note {
          margin-top: 18px;
          padding-top: 15px;
          border-top: 1px solid rgba(255,255,255,.1);
          color: #94a3b8;
          font-size: 11px;
          line-height: 1.6;
        }
        .spin { animation: spin 1s linear infinite; }
        @keyframes spin {
          from { transform: rotate(0); }
          to { transform: rotate(360deg); }
        }
      \`}</style>
    </main>
  );
}
