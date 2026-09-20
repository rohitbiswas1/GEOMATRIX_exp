'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Bell,
  BrainCircuit,
  Database,
  FileText,
  LayoutDashboard,
  Map,
  Search,
  ShieldCheck,
  Users,
  LogOut,
  Sun,
  Moon,
  Laptop,
  Clock,
  Cpu
} from 'lucide-react';
import { useEffect, useState } from 'react';

type ThemeMode = 'system' | 'light' | 'dark';

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const [q, setQ] = useState('');
  const [themeMode, setThemeMode] = useState<ThemeMode>('light');
  const [userInfo, setUserInfo] = useState<{ role?: string; email?: string } | null>(null);

  const login = path === '/login';

  // Auth check + user info
  useEffect(() => {
    if (!login && !sessionStorage.getItem('geomatrix-auth')) {
      router.replace('/login');
    }
    const auth = sessionStorage.getItem('geomatrix-auth');
    if (auth) {
      try { setUserInfo(JSON.parse(auth)); } catch { /* ignore */ }
    }
  }, [login, router]);

  // Theme synchronization - default to light
  useEffect(() => {
    const saved = localStorage.getItem('geomatrix-theme') as ThemeMode | null;
    if (saved) {
      setThemeMode(saved);
    } else {
      setThemeMode('light');
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('geomatrix-theme', themeMode);
    const media = window.matchMedia('(prefers-color-scheme: dark)');

    const applyTheme = () => {
      const active = themeMode === 'system' ? (media.matches ? 'dark' : 'light') : themeMode;
      document.documentElement.setAttribute('data-theme', active);
    };

    applyTheme();
    media.addEventListener('change', applyTheme);
    return () => media.removeEventListener('change', applyTheme);
  }, [themeMode]);

  if (login) return <>{children}</>;

  const logout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } finally {
      sessionStorage.removeItem('geomatrix-auth');
      router.replace('/login');
    }
  };

  const nav = [
    ['/dashboard', 'Command Center', LayoutDashboard],
    ['/projects', 'Projects', Users],
    ['/map', 'GIS Risk Map', Map],
    ['/alerts', 'Alerts', Bell],
    ['/analytics', 'Analytics', BrainCircuit],
    ['/reports', 'Reports', FileText],
    ['/data', 'Data Management', Database],
    ['/model', 'Model Intelligence', Cpu],
  ] as const;

  const handleSearchSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && q.trim()) {
      router.push('/projects?search=' + encodeURIComponent(q.trim()));
    }
  };

  const sectionName =
    path === '/dashboard'
      ? 'Command Center'
      : path.split('/')[1]?.charAt(0).toUpperCase() + path.split('/')[1]?.slice(1) || 'Dashboard';

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandmark">
            <Map size={19} />
          </div>
          <div>
            <b>GEOMATRIX</b>
            <small>LAND ACQUISITION AI</small>
          </div>
        </div>

        <nav className="nav">
          {nav.map(([href, label, Icon]) => {
            const isActive = path.startsWith(href);
            return (
              <Link key={href} href={href} className={isActive ? 'active' : ''}>
                <Icon size={16} />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebottom">
          <div className="userline">
            <div>
              <b style={{ fontSize: 13 }}>Authenticated Operator</b>
              <div className="role">{userInfo?.email || 'Signed-in user'}</div>
            </div>
            <ShieldCheck size={16} color="#60a5fa" />
          </div>
          <button className="btn" style={{ marginTop: 12, width: '100%' }} onClick={logout}>
            <LogOut size={13} /> Logout
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="crumb">
            GovTech Decision Support / <strong>{sectionName}</strong>
          </div>

          <div className="search">
            <Search className="search-icon" size={14} />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={handleSearchSubmit}
              placeholder="Search project code, name, district, or agency…"
              aria-label="Search projects"
            />
            <span className="search-kbd">↵ Enter</span>
          </div>

          <div className="topright">
            <div className="status-badge" title="Automated pipeline active">
              <span className="pulse-dot" />
              <span>System Operational</span>
            </div>

            <div className="topbar-date">
              <Clock size={13} />
              <span>{new Intl.DateTimeFormat('en-IN',{dateStyle:'medium',timeStyle:'short',timeZone:'Asia/Kolkata'}).format(new Date())} IST</span>
            </div>

            <button
              className="topbar-icon-btn"
              title="5 Priority Alerts"
              onClick={() => router.push('/alerts')}
              aria-label="View alerts"
            >
              <Bell size={15} />
              <span className="topbar-badge">5</span>
            </button>

            <div className="theme-switch-group" role="radiogroup" aria-label="Theme selector">
              <button
                type="button"
                className={`theme-switch-btn ${themeMode === 'light' ? 'active' : ''}`}
                onClick={() => setThemeMode('light')}
                title="Light mode"
                aria-checked={themeMode === 'light'}
              >
                <Sun size={13} />
              </button>
              <button
                type="button"
                className={`theme-switch-btn ${themeMode === 'dark' ? 'active' : ''}`}
                onClick={() => setThemeMode('dark')}
                title="Dark mode"
                aria-checked={themeMode === 'dark'}
              >
                <Moon size={13} />
              </button>
              <button
                type="button"
                className={`theme-switch-btn ${themeMode === 'system' ? 'active' : ''}`}
                onClick={() => setThemeMode('system')}
                title="Follow system theme"
                aria-checked={themeMode === 'system'}
              >
                <Laptop size={13} />
              </button>
            </div>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}
