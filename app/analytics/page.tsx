'use client';

import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { RefreshCw, BarChart3, Database } from 'lucide-react';
import { ApiError } from '../../lib/apiClient';

type Overview = {
  totalProjects: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  scoredProjects: number;
  avgRiskScore: number | null;
  avgDelayProbability: number | null;
  totalLandHa: number;
  totalFamilies: number;
  alertsOpen: number;
};

type Driver = { feature: string; mean_abs_shap: number; sample_count: number };
type Stage = { stage: string; projects: number; avgRiskScore: number | null };

export default function Analytics() {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [stages, setStages] = useState<Stage[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [o, d, s] = await Promise.all([
        fetch('/backend/api/analytics/overview', { cache: 'no-store' }).then(r => r.json()),
        fetch('/backend/api/analytics/drivers', { cache: 'no-store' }).then(r => r.json()),
        fetch('/backend/api/analytics/stages', { cache: 'no-store' }).then(r => r.json()),
      ]);
      if (o?.error || d?.error || s?.error) throw new Error(o?.error || d?.error || s?.error);
      setOverview(o);
      setDrivers(Array.isArray(d) ? d : []);
      setStages(Array.isArray(s) ? s : []);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : e instanceof Error ? e.message : 'Analytics unavailable.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="page">
      <div className="head">
        <div>
          <div className="eyebrow"><BarChart3 size={11} /> Portfolio intelligence</div>
          <h1 className="h1">Analytics</h1>
          <div className="sub">All values are calculated from persisted project and model-output records.</div>
        </div>
        <button className="btn" onClick={load} disabled={loading} style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {error && <div className="panel" style={{ borderColor: 'var(--red)', color: 'var(--red-text)', marginBottom: 16 }}>{error}</div>}

      <div className="grid six" style={{ marginBottom: 16 }}>
        {[
          ['Projects', overview?.totalProjects ?? 0],
          ['Scored', overview?.scoredProjects ?? 0],
          ['Critical', overview?.critical ?? 0],
          ['High', overview?.high ?? 0],
          ['Open alerts', overview?.alertsOpen ?? 0],
          ['Avg risk', overview?.avgRiskScore == null ? '—' : overview.avgRiskScore.toFixed(1)],
        ].map(([label, value]) => (
          <div className="kpi" key={String(label)}>
            <div className="label">{label}</div>
            <div className="value" style={{ fontSize: 22 }}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid two">
        <div className="panel">
          <div className="paneltitle">Global delay drivers</div>
          {drivers.length === 0 ? (
            <div className="muted" style={{ marginTop: 18 }}>No prediction history is available yet.</div>
          ) : (
            <div className="chart" style={{ height: 300, marginTop: 10 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={drivers.slice(0, 10)} layout="vertical" margin={{ left: 90, right: 15 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis type="number" fontSize={10} />
                  <YAxis type="category" dataKey="feature" width={130} fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="mean_abs_shap" fill="var(--blue)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="panel">
          <div className="paneltitle">Risk by acquisition stage</div>
          {stages.length === 0 ? (
            <div className="muted" style={{ marginTop: 18 }}>No project records are available yet.</div>
          ) : (
            <div className="chart" style={{ height: 300, marginTop: 10 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stages.slice(0, 10)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis dataKey="stage" angle={-25} textAnchor="end" height={80} fontSize={9} />
                  <YAxis fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="avgRiskScore" fill="var(--green)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="paneltitle"><Database size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Portfolio data coverage</div>
        <div className="grid four" style={{ marginTop: 12 }}>
          {[
            ['Average delay probability', overview?.avgDelayProbability == null ? '—' : `${(overview.avgDelayProbability * 100).toFixed(1)}%`],
            ['Land required', `${overview?.totalLandHa ?? 0} ha`],
            ['Affected families', overview?.totalFamilies ?? 0],
            ['Unscored projects', Math.max(0, (overview?.totalProjects ?? 0) - (overview?.scoredProjects ?? 0))],
          ].map(([label, value]) => (
            <div className="rec" key={label}><b>{label}</b><p>{value}</p></div>
          ))}
        </div>
      </div>
    </div>
  );
}
