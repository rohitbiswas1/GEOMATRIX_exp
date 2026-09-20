'use client';

import { useEffect, useState } from 'react';
import { Download, FileText, RefreshCw, Printer } from 'lucide-react';
import { fetchDashboardSummary, fetchProjects, ApiProject, DashboardSummary } from '../../lib/apiClient';
import { exportToCSV, exportToPDF } from '../../lib/exportUtils';

const types = ['Executive Risk Summary', 'District Risk Report', 'Project Risk Report', 'Delay Driver Report', 'Intervention Report'] as const;

export default function Reports() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [projects, setProjects] = useState<ApiProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const [s, p] = await Promise.all([fetchDashboardSummary(), fetchProjects({ limit: 500 })]);
      setSummary(s);
      setProjects(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unable to load report data.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  function rowsForProjects() {
    return projects.map(p => [
      p.project_code,
      p.name,
      p.state,
      p.district,
      p.authority,
      p.current_stage ?? '',
      p.risk_score ?? '',
      p.risk_level ?? '',
      p.delay_probability == null ? '' : (p.delay_probability * 100).toFixed(2) + '%',
      p.predicted_delay_days ?? '',
      p.data_classification ?? '',
      p.validation_status ?? '',
      p.source_name ?? '',
      p.source_url ?? '',
    ]);
  }

  function downloadCsv() {
    const headers = ['Project Code','Project Name','State','District','Authority','Stage','Risk Score','Risk Level','Delay Probability','Predicted Delay Days','Classification','Validation Status','Source','Source URL'];
    exportToCSV('geomatrix-government-project-register.csv', headers, rowsForProjects());
  }

  function printReport() {
    window.print();
  }

  function downloadPdf() {
    const headers = ['Project Code','Project Name','State','District','Stage','Risk Score','Risk Level','Delay Probability','Classification'];
    exportToPDF(
      'GEOMATRIX Government Project Risk Register',
      'Live database-backed project and ML outputs',
      headers,
      projects.map(p => [p.project_code,p.name,p.state,p.district,p.current_stage ?? '',p.risk_score ?? '',p.risk_level ?? '',p.delay_probability == null ? '' : (p.delay_probability * 100).toFixed(2) + '%',p.data_classification ?? '']),
      'geomatrix-government-project-risk-register.pdf',
      [
        { label: 'Projects', value: summary?.total_projects ?? 0 },
        { label: 'Critical', value: summary?.critical_count ?? 0 },
        { label: 'High', value: summary?.high_count ?? 0 },
        { label: 'Open Alerts', value: summary?.alerts_open ?? 0 },
      ],
    );
  }

  return (
    <div className="page">
      <div className="head">
        <div>
          <div className="eyebrow"><FileText size={11} /> Government reporting</div>
          <h1 className="h1">Reports</h1>
          <div className="sub">Reports are generated from live persisted records. No simulated portfolio totals are included.</div>
        </div>
        <div className="actions">
          <button className="btn" onClick={load} disabled={loading}><RefreshCw size={13} /> Refresh</button>
          <button className="btn" onClick={printReport}><Printer size={13} /> Print</button>
          <button className="btn" onClick={downloadCsv}><Download size={13} /> CSV</button>
          <button className="btn primary" onClick={downloadPdf}><Download size={13} /> PDF</button>
        </div>
      </div>

      {error && <div className="panel" style={{ borderColor: 'var(--red)', color: 'var(--red-text)', marginBottom: 16 }}>{error}</div>}

      <div className="grid four" style={{ marginBottom: 18 }}>
        {[
          ['Projects', summary?.total_projects ?? 0],
          ['Critical', summary?.critical_count ?? 0],
          ['High', summary?.high_count ?? 0],
          ['Open Alerts', summary?.alerts_open ?? 0],
        ].map(([label, value]) => <div className="kpi" key={label}><div className="label">{label}</div><div className="value" style={{ fontSize: 24 }}>{value}</div></div>)}
      </div>

      <div className="grid cards">
        {types.map(type => (
          <div className="panel" key={type}>
            <FileText size={20} style={{ color: 'var(--blue)' }} />
            <h3 style={{ fontSize: 14 }}>{type}</h3>
            <p className="sub">Use the live project register and model outputs as the report source.</p>
            <button className="btn" onClick={printReport}>Print preview</button>
          </div>
        ))}
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="eyebrow">Data provenance</div>
        <h2>Live project register</h2>
        <p className="sub">Rows: {projects.length}. Unscored or unvalidated records remain visible and are not assigned fabricated risk values.</p>
        {loading ? <div className="muted">Loading…</div> : projects.length === 0 ? <div className="muted">No persisted projects.</div> : (
          <div className="tablewrap">
            <table className="table">
              <thead><tr><th>Code</th><th>Project</th><th>State</th><th>Stage</th><th>Risk</th><th>Classification</th></tr></thead>
              <tbody>{projects.slice(0, 25).map(p => <tr key={p.id}>
                <td>{p.project_code}</td><td>{p.name}</td><td>{p.state}</td><td>{p.current_stage ?? '—'}</td>
                <td>{p.risk_score == null ? '—' : p.risk_score.toFixed(1)}</td><td>{p.data_classification ?? '—'}</td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
