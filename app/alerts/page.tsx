'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AlertCircle, AlertTriangle, Bell, CheckCircle2, Filter, RefreshCw } from 'lucide-react';
import { fetchAlerts, ApiAlert } from '../../lib/apiClient';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<ApiAlert[]>([]);
  const [severity, setSeverity] = useState('All');
  const [status, setStatus] = useState('All');
  const [selected, setSelected] = useState<ApiAlert | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  async function load() {
    setLoading(true);
    setMessage('');
    try {
      const data = await fetchAlerts('All', 200);
      setAlerts(data);
    } catch (error) {
      setAlerts([]);
      setMessage(error instanceof Error ? error.message : 'Unable to load alerts.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function updateStatus(alert: ApiAlert, nextStatus: 'Acknowledged' | 'Resolved') {
    try {
      const response = await fetch(`/api/alerts/${encodeURIComponent(alert.id)}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.detail || data?.error || 'Alert update failed.');
      setAlerts(prev => prev.map(item => item.id === alert.id ? { ...item, status: nextStatus } : item));
      setSelected(prev => prev?.id === alert.id ? { ...prev, status: nextStatus } : prev);
      setMessage(`Alert ${nextStatus.toLowerCase()}.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Alert update failed.');
    }
  }

  const filtered = useMemo(() => alerts.filter(alert => {
    const severityMatch = severity === 'All' || alert.severity === severity;
    const statusMatch = status === 'All' || alert.status === status;
    return severityMatch && statusMatch;
  }), [alerts, severity, status]);

  const counts = useMemo(() => ({
    critical: alerts.filter(a => a.severity === 'Critical').length,
    high: alerts.filter(a => a.severity === 'High').length,
    medium: alerts.filter(a => a.severity === 'Medium').length,
    open: alerts.filter(a => a.status === 'Open').length,
    acknowledged: alerts.filter(a => a.status === 'Acknowledged').length,
    resolved: alerts.filter(a => a.status === 'Resolved').length,
  }), [alerts]);

  return (
    <div className="page">
      <div className="head">
        <div>
          <div className="eyebrow"><Bell size={11} /> Early warning</div>
          <h1 className="h1">Predictive Alerts</h1>
          <div className="sub">Alert records are read from and updated in the persisted backend database.</div>
        </div>
        <button className="btn" onClick={load} disabled={loading}><RefreshCw size={13} /> Refresh</button>
      </div>

      {message && <div className="panel" style={{ marginBottom: 16, borderColor: 'var(--line)' }}>{message}</div>}

      <div className="grid six" style={{ marginBottom: 18 }}>
        {[
          ['Critical', counts.critical], ['High', counts.high], ['Medium', counts.medium],
          ['Open', counts.open], ['Acknowledged', counts.acknowledged], ['Resolved', counts.resolved],
        ].map(([label, value]) => <div className="kpi" key={label}><div className="label">{label}</div><div className="value" style={{ fontSize: 22 }}>{value}</div></div>)}
      </div>

      <div className="filter-bar" style={{ marginBottom: 16 }}>
        <div className="filter-group">
          <Filter size={14} style={{ color: 'var(--muted)' }} />
          <div className="filter-item">
            <label className="filter-label">Severity</label>
            <select className="filter-select" value={severity} onChange={e => setSeverity(e.target.value)}>
              <option>All</option><option>Critical</option><option>High</option><option>Medium</option>
            </select>
          </div>
          <div className="filter-item">
            <label className="filter-label">Status</label>
            <select className="filter-select" value={status} onChange={e => setStatus(e.target.value)}>
              <option>All</option><option>Open</option><option>Acknowledged</option><option>Resolved</option>
            </select>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: selected ? '1fr 360px' : '1fr', gap: 16 }}>
        <div className="panel" style={{ padding: 0 }}>
          <div className="tablewrap">
            <table className="table">
              <thead><tr><th>Severity</th><th>Alert</th><th>Project</th><th>Detected</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center' }}><RefreshCw size={18} style={{ animation: 'spin 1s linear infinite' }} /></td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>No persisted alerts match these filters.</td></tr>
                ) : filtered.map(alert => (
                  <tr key={alert.id} onClick={() => setSelected(selected?.id === alert.id ? null : alert)} style={{ cursor: 'pointer' }}>
                    <td>
                      <span className={`risk ${alert.severity.toLowerCase()}`} style={{ display: 'inline-flex', gap: 5, alignItems: 'center' }}>
                        {alert.severity === 'Critical' ? <AlertTriangle size={13} /> : alert.severity === 'High' ? <AlertCircle size={13} /> : <Bell size={13} />}
                        {alert.severity}
                      </span>
                    </td>
                    <td><div style={{ fontWeight: 700 }}>{alert.reason}</div></td>
                    <td><Link className="link" href={`/projects/${alert.project_id}`} onClick={e => e.stopPropagation()}>{alert.project_name ?? alert.project_id}</Link></td>
                    <td>{new Date(alert.detected_at).toLocaleString('en-IN')}</td>
                    <td>{alert.status}</td>
                    <td onClick={e => e.stopPropagation()}>
                      <div className="actions">
                        {alert.status === 'Open' && <button className="btn" onClick={() => updateStatus(alert, 'Acknowledged')}><CheckCircle2 size={12} /> Acknowledge</button>}
                        {alert.status !== 'Resolved' && <button className="btn" onClick={() => updateStatus(alert, 'Resolved')}><CheckCircle2 size={12} /> Resolve</button>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {selected && (
          <aside className="panel">
            <div className="paneltitle">Alert details</div>
            <div style={{ display: 'grid', gap: 10, marginTop: 14 }}>
              <div><span className="muted">Project</span><div style={{ fontWeight: 700, marginTop: 3 }}>{selected.project_name ?? selected.project_id}</div></div>
              <div><span className="muted">Severity</span><div style={{ fontWeight: 700, marginTop: 3 }}>{selected.severity}</div></div>
              <div><span className="muted">Reason</span><div style={{ marginTop: 3, lineHeight: 1.5 }}>{selected.reason}</div></div>
              <div><span className="muted">Recommended action</span><div style={{ marginTop: 3, lineHeight: 1.5 }}>{selected.recommended_action ?? 'Review the project record.'}</div></div>
              <div><span className="muted">Detected</span><div style={{ marginTop: 3 }}>{new Date(selected.detected_at).toLocaleString('en-IN')}</div></div>
              <div><span className="muted">Status</span><div style={{ marginTop: 3 }}>{selected.status}</div></div>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
