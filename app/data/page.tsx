'use client';

import { useCallback, useEffect, useState } from 'react';
import { Upload, Database, AlertCircle, RefreshCw, FileText } from 'lucide-react';
import {
  uploadFile,
  fetchIngestionLog,
  fetchTrainingDataSummary,
  fetchDashboardSummary,
  IngestionLogEntry,
  TrainingDataSummary,
  DashboardSummary,
} from '../../lib/apiClient';

type UploadItem = { name: string; status: string; saved?: number; skipped?: number; error?: string };

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DataPage() {
  const [dataType, setDataType] = useState<'projects' | 'historical'>('projects');
  const [items, setItems] = useState<UploadItem[]>([]);
  const [logs, setLogs] = useState<IngestionLogEntry[]>([]);
  const [training, setTraining] = useState<TrainingDataSummary | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [l, t, s] = await Promise.all([fetchIngestionLog(25), fetchTrainingDataSummary(), fetchDashboardSummary()]);
      setLogs(l);
      setTraining(t);
      setSummary(s);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function onFiles(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = Array.from(event.target.files ?? []);
    for (const file of selected) {
      setItems(prev => [...prev, { name: file.name, status: 'uploading' }]);
      try {
        const result = await uploadFile(file, dataType);
        setItems(prev => prev.map(item => item.name === file.name ? {
          ...item,
          status: result.status,
          saved: result.records_saved,
          skipped: result.records_skipped,
          error: result.errors[0],
        } : item));
      } catch (error) {
        setItems(prev => prev.map(item => item.name === file.name ? {
          ...item,
          status: 'error',
          error: error instanceof Error ? error.message : 'Upload failed',
        } : item));
      }
    }
    await load();
    event.target.value = '';
  }

  return (
    <div className="page">
      <div className="head">
        <div>
          <div className="eyebrow"><Database size={11} /> Data governance</div>
          <h1 className="h1">Data Operations</h1>
          <div className="sub">Controlled ingestion, provenance, validation and training-data monitoring.</div>
        </div>
        <button className="btn" onClick={load} disabled={loading}><RefreshCw size={13} /> Refresh</button>
      </div>

      <div className="grid four" style={{ marginBottom: 16 }}>
        {[
          ['Projects in DB', summary?.total_projects ?? 0],
          ['Historical records', training?.total_records ?? 0],
          ['Delayed labels', training?.delayed_count ?? 0],
          ['On-time labels', training?.on_time_count ?? 0],
        ].map(([label, value]) => <div className="kpi" key={label}><div className="label">{label}</div><div className="value" style={{ fontSize: 24 }}>{value}</div></div>)}
      </div>

      <div className="panel">
        <div className="paneltitle">Controlled upload</div>
        <div className="sub" style={{ margin: '8px 0 14px' }}>
          Uploaded data is not treated as official/REAL by default. Historical training records require explicit provenance and approval before entering the ML training pool.
        </div>
        <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
          <button className={`btn ${dataType === 'projects' ? 'primary' : ''}`} onClick={() => setDataType('projects')}>Project records</button>
          <button className={`btn ${dataType === 'historical' ? 'primary' : ''}`} onClick={() => setDataType('historical')}>Historical training records</button>
        </div>
        <label className="btn" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, padding: '22px', borderStyle: 'dashed', cursor: 'pointer' }}>
          <Upload size={18} /> Upload CSV / JSON
          <input type="file" multiple accept=".csv,.json" style={{ display: 'none' }} onChange={onFiles} />
        </label>
        {items.length > 0 && <div style={{ marginTop: 16, display: 'grid', gap: 8 }}>
          {items.map((item, index) => <div key={`${item.name}-${index}`} className="rec">
            <div style={{ fontWeight: 700 }}>{item.name}</div>
            <div className="muted" style={{ marginTop: 4 }}>{item.status}{item.saved != null ? ` · saved ${item.saved} · skipped ${item.skipped}` : ''}</div>
            {item.error && <div style={{ color: 'var(--red-text)', fontSize: 12, marginTop: 4 }}><AlertCircle size={12} style={{ verticalAlign: 'middle' }} /> {item.error}</div>}
          </div>)}
        </div>}
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="panelhead">
          <div><div className="paneltitle">Training-data gate</div><div className="muted">{training?.message ?? 'Loading…'}</div></div>
          <span className={`risk ${training?.ready_to_train ? 'low' : 'critical'}`}>{training?.ready_to_train ? 'Eligible' : 'Blocked'}</span>
        </div>
        <div className="muted" style={{ marginTop: 12, lineHeight: 1.7 }}>
          Model training is intentionally disabled at runtime by default. Use the offline training procedure on an approved snapshot, review validation metrics, preserve the dataset fingerprint, then deploy the approved model bundle.
        </div>
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="paneltitle"><FileText size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} /> Ingestion log</div>
        {logs.length === 0 ? <div className="muted" style={{ marginTop: 12 }}>No ingestion events recorded.</div> : (
          <div className="tablewrap" style={{ marginTop: 10 }}>
            <table className="table"><thead><tr><th>Started</th><th>Source</th><th>Fetched</th><th>Saved</th><th>Skipped</th><th>Status</th></tr></thead>
              <tbody>{logs.map(log => <tr key={log.id}>
                <td>{new Date(log.started_at).toLocaleString('en-IN')}</td><td>{log.source}</td><td>{log.records_fetched}</td><td>{log.records_saved}</td><td>{log.records_skipped}</td><td>{log.status}</td>
              </tr>)}</tbody>
            </table>
          </div>
        )}
      </div>
      <div className="muted" style={{ marginTop: 10, fontSize: 11 }}>Selected file sizes are checked by the server. Client-side display: {items.map(i=>i.name).join(', ') || 'none'}.</div>
    </div>
  );
}
