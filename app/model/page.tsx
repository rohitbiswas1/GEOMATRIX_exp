'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { RefreshCw, ShieldCheck, AlertTriangle, Database, BrainCircuit } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import {
  fetchModelStatus,
  fetchTrainingDataSummary,
  ModelStatus,
  TrainingDataSummary,
  ApiError,
} from '../../lib/apiClient';

const LABELS: Record<string, string> = {
  land_area_ha: 'Land area',
  affected_families: 'Affected families',
  pending_claims: 'Pending claims',
  legal_cases: 'Legal cases',
  doc_completeness_pct: 'Documentation completeness',
  approval_pending: 'Approval pending',
  rr_pending: 'R&R pending',
  overdue_milestones: 'Overdue milestones',
  compensation_pending: 'Compensation pending',
  env_clearance_pending: 'Clearance pending',
};

function pct(value?: number | null): string {
  return value == null ? '—' : `${(value * 100).toFixed(1)}%`;
}

export default function ModelIntelligence() {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [summary, setSummary] = useState<TrainingDataSummary | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [model, data] = await Promise.all([
        fetchModelStatus(),
        fetchTrainingDataSummary(),
      ]);
      setStatus(model);
      setSummary(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unable to load model telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const features = useMemo(() => {
    return Object.entries(status?.feature_importance ?? {})
      .map(([key, value]) => ({ name: LABELS[key] ?? key, value: Number(value) }))
      .sort((a, b) => b.value - a.value);
  }, [status]);

  const classCounts = status?.class_counts ?? {};

  return (
    <div className="page">
      <div className="head">
        <div>
          <div className="eyebrow"><BrainCircuit size={11} /> Model Governance</div>
          <h1 className="h1">AI Model Intelligence</h1>
          <div className="sub">
            Auditable model status, approved training data, validation metrics and explainability.
            No simulated performance metrics are displayed.
          </div>
        </div>
        <button className="btn" onClick={load} disabled={loading} style={{ display: 'inline-flex', gap: 7, alignItems: 'center' }}>
          <RefreshCw size={14} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="panel" style={{ borderColor: 'var(--red)', color: 'var(--red-text)', marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div className="panel" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 20, flexWrap: 'wrap' }}>
          <div>
            <div className="eyebrow"><ShieldCheck size={11} /> Deployment State</div>
            <div style={{ fontSize: 22, fontWeight: 900, marginTop: 5 }}>
              {status?.trained ? 'Validated model deployed' : 'No validated model deployed'}
            </div>
            <div className="muted" style={{ marginTop: 5 }}>
              {status?.message ?? 'Loading model state…'}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="label">Model version</div>
            <div style={{ fontWeight: 800 }}>{status?.model_version ?? '—'}</div>
            <div className="label" style={{ marginTop: 8 }}>Algorithm</div>
            <div style={{ fontWeight: 800 }}>{status?.algorithm ?? '—'}</div>
          </div>
        </div>
      </div>

      <div className="grid six" style={{ marginBottom: 16 }}>
        {[
          ['Samples', status?.n_samples ?? summary?.total_records ?? 0],
          ['Delayed labels', classCounts['1'] ?? summary?.delayed_count ?? 0],
          ['On-time labels', classCounts['0'] ?? summary?.on_time_count ?? 0],
          ['Precision', pct(status?.precision)],
          ['Recall', pct(status?.recall)],
          ['F1', pct(status?.f1_score)],
        ].map(([label, value]) => (
          <div className="kpi" key={String(label)}>
            <div className="label">{label}</div>
            <div className="value" style={{ fontSize: 22 }}>{value}</div>
          </div>
        ))}
      </div>

      <div className="grid two">
        <div className="panel">
          <div className="paneltitle">Validation metrics</div>
          <div style={{ display: 'grid', gap: 10, marginTop: 15 }}>
            {[
              ['Accuracy', pct(status?.accuracy)],
              ['ROC-AUC', pct(status?.roc_auc)],
              ['CV ROC-AUC', status?.cv_roc_auc_mean == null ? '—' : `${pct(status.cv_roc_auc_mean)} ± ${pct(status.cv_roc_auc_std)}`],
              ['CV F1', status?.cv_f1_mean == null ? '—' : `${pct(status.cv_f1_mean)} ± ${pct(status.cv_f1_std)}`],
              ['CV folds', status?.cv_folds ?? '—'],
              ['Regression head', status?.regression_target_available ? 'Enabled' : 'Unavailable'],
            ].map(([label, value]) => (
              <div key={String(label)} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--line)', paddingBottom: 9 }}>
                <span className="muted">{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="paneltitle">Global feature importance</div>
          {features.length === 0 ? (
            <div className="muted" style={{ marginTop: 18 }}>Feature importance becomes available after an approved model is trained.</div>
          ) : (
            <div className="chart" style={{ height: 300, marginTop: 10 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={features} layout="vertical" margin={{ left: 80, right: 15 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                  <XAxis type="number" fontSize={10} />
                  <YAxis type="category" dataKey="name" width={115} fontSize={10} />
                  <Tooltip />
                  <Bar dataKey="value" fill="var(--blue)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="paneltitle">Training data gate</div>
        <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {summary?.ready_to_train ? <ShieldCheck size={15} /> : <AlertTriangle size={15} />}
            <strong>{summary?.ready_to_train ? 'Dataset passes the minimum classification gate' : 'Training is blocked'}</strong>
          </div>
          <div className="muted">{summary?.message ?? 'Loading training-data status…'}</div>
          <div className="muted" style={{ fontSize: 12 }}>
            Runtime training is disabled by default. Model training should be performed offline against an approved, versioned government dataset, then the validated artifact should be deployed.
          </div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 16 }}>
        <div className="paneltitle">Model governance notes</div>
        <div className="muted" style={{ marginTop: 12, lineHeight: 1.7 }}>
          <div><Database size={13} style={{ verticalAlign: 'middle', marginRight: 6 }} />Only records classified as REAL and validated/approved are eligible for training.</div>
          <div>Prediction certainty is reported separately from validation metrics and is constrained to 0–100%.</div>
          <div>No delay-days forecast is shown unless an approved regression target is available for the complete training set.</div>
          <div>The current repository intentionally contains no active trained model artifact until an approved model is produced from the official training dataset.</div>
        </div>
      </div>
    </div>
  );
}
