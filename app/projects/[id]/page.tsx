'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useState, useMemo, useEffect, useCallback } from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, BarChart, Bar, Cell
} from 'recharts';
import {
  ArrowLeft, AlertTriangle, CheckCircle2, TrendingUp, TrendingDown,
  Minus, Brain, Activity, Sliders, GitBranch, Database, ArrowUpRight,
  Clock, User, MapPin, Zap, Target, FileWarning, RefreshCw, Sparkles, AlertCircle, Trash2
} from 'lucide-react';
import {
  fetchProject, runPrediction, fetchExplanation, explainWithGemini, validateProject,
  deleteProject, createProjectAction, fetchProjectAudit, ApiProject, ShapFeature, PredictionResult, ApiError, AuditLogEntry
} from '../../../lib/apiClient';
import { riskLevel, stages, type RiskLevel } from '../../../lib/risk';
import ExportDropdown, { ExportFormat } from '../../../components/ExportDropdown';
import { exportToCSV, exportToExcel, exportToPDF } from '../../../lib/exportUtils';

// ─── Risk colour helpers ──────────────────────────────────────────────────────
const RISK_COLORS: Record<RiskLevel, string> = {
  Critical: '#dc2626', High: '#ea580c', Medium: '#d97706', Low: '#15803d'
};
const RISK_BG: Record<RiskLevel, string> = {
  Critical: 'rgba(220,38,38,0.08)', High: 'rgba(234,88,12,0.08)',
  Medium: 'rgba(217,119,6,0.08)', Low: 'rgba(21,128,91,0.08)'
};

// ─── Small components ─────────────────────────────────────────────────────────

function RiskBadge({ score }: { score: number }) {
  const rl = riskLevel(score);
  return (
    <span className={'risk ' + rl.toLowerCase()} style={{ fontSize: 12, fontWeight: 700 }}>
      {rl}
    </span>
  );
}

function TrendBadge({ trend }: { trend: string }) {
  if (trend === 'rising') return <span style={{ color: '#dc2626', fontWeight: 700, fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 3 }}><TrendingUp size={13} /> Rising</span>;
  if (trend === 'falling') return <span style={{ color: '#15803d', fontWeight: 700, fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 3 }}><TrendingDown size={13} /> Falling</span>;
  return <span style={{ color: '#6b7280', fontWeight: 700, fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 3 }}><Minus size={13} /> Stable</span>;
}

function MetricCard({ label, value, sub, color, icon }: { label: string; value: string; sub?: string; color?: string; icon?: React.ReactNode }) {
  return (
    <div className="kpi" style={{ minHeight: 80 }}>
      <div className="kpi-head">
        <div className="label">{label}</div>
        {icon}
      </div>
      <div className="value" style={{ fontSize: 24, color: color || 'var(--ink)' }}>{value}</div>
      {sub && <div className="trend" style={{ fontSize: 11 }}>{sub}</div>}
    </div>
  );
}

// ─── Tab definitions ──────────────────────────────────────────────────────────
const TABS = [
  { key: 'shap', label: 'AI Risk Analysis', icon: Brain },
  { key: 'forecast', label: 'Forecast & Prediction', icon: Activity },
  { key: 'simulator', label: 'What-If Simulator', icon: Sliders },
  { key: 'intervention', label: 'Interventions', icon: Target },
  { key: 'timeline', label: 'Acquisition Pipeline', icon: GitBranch },
  { key: 'lineage', label: 'Data Lineage', icon: Database },
] as const;
type TabKey = typeof TABS[number]['key'];

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ProjectRiskIntelligence() {
  const { id } = useParams<{ id: string }>();

  // ── Real API state ───────────────────────────────────────────────────────
  const [p, setP] = useState<ApiProject | null>(null);
  const [loadingProject, setLoadingProject] = useState(true);
  const [projectError, setProjectError] = useState('');
  const [shapFeatures, setShapFeatures] = useState<ShapFeature[]>([]);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);
  const [runningPrediction, setRunningPrediction] = useState(false);
  const [predictionError, setPredictionError] = useState('');
  const [missingFields, setMissingFields] = useState<string[]>([]);
  const [geminiResult, setGeminiResult] = useState('');
  const [geminiLoading, setGeminiLoading] = useState(false);
  const [geminiError, setGeminiError] = useState('');
  const [auditEntries, setAuditEntries] = useState<AuditLogEntry[]>([]);

  const loadProject = useCallback(async () => {
    setLoadingProject(true);
    setProjectError('');
    try {
      const data = await fetchProject(id as string);
      setP(data);
      try {
        const [v, audit] = await Promise.all([
          validateProject(id as string),
          fetchProjectAudit(id as string),
        ]);
        setMissingFields(v.missing_fields);
        setAuditEntries(audit);
      } catch {
        setAuditEntries([]);
      }
    } catch (e) {
      setProjectError(e instanceof ApiError ? `Error ${e.status}: ${e.message}` : 'Failed to load project');
    } finally {
      setLoadingProject(false);
    }
  }, [id]);

  useEffect(() => { loadProject(); }, [loadProject]);

  async function handleRunPrediction() {
    if (!p) return;
    setRunningPrediction(true);
    setPredictionError('');
    try {
      const res = await runPrediction(p.id);
      setPrediction(res.prediction);
      setShapFeatures(res.prediction.shap_features ?? []);
      await loadProject();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : 'Prediction failed';
      let friendly = msg;
      try { const parsed = JSON.parse(msg); friendly = parsed.detail ?? msg; } catch { /* ignore */ }
      setPredictionError(friendly);
    } finally {
      setRunningPrediction(false);
    }
  }

  async function handleDeleteProject() {
    if (!p) return;
    const ok = window.confirm(`Delete project "${p.name}"? This action cannot be undone.`);
    if (!ok) return;

    try {
      await deleteProject(p.id);
      window.location.href = '/projects';
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Deletion failed';
      setProjectError(msg);
    }
  }

  async function handleGeminiExplain() {
    if (!p) return;
    setGeminiLoading(true);
    setGeminiError('');
    setGeminiResult('');
    try {
      const res = await explainWithGemini({
        project: p as unknown as Record<string, unknown>,
        prediction: prediction ? (prediction as unknown as Record<string, unknown>) : undefined,
        shap_features: shapFeatures.length > 0 ? shapFeatures : undefined,
      });
      setGeminiResult(res.summary);
    } catch (e) {
      setGeminiError(e instanceof ApiError ? e.message : 'Gemini explain failed');
    } finally {
      setGeminiLoading(false);
    }
  }

  const [activeTab, setActiveTab] = useState<TabKey>('shap');
  const [modal, setModal] = useState(false);
  const [toast, setToast] = useState('');
  const [assignedTo, setAssignedTo] = useState('District Land Acquisition Officer (DLAO)');
  const [priority, setPriority] = useState<'Critical' | 'High' | 'Medium' | 'Low'>('High');
  const [dueDate, setDueDate] = useState('');
  const [interventionNote, setInterventionNote] = useState('');
  const [actionSaving, setActionSaving] = useState(false);

  // ── Derived display values ───────────────────────────────────────────────
  const riskScore = prediction?.risk_score ?? p?.risk_score;
  const riskLevelStr = riskScore != null ? (prediction?.risk_level ?? p?.risk_level ?? riskLevel(riskScore)) as RiskLevel : null;
  const rl = riskLevelStr;
  const riskColor = rl ? RISK_COLORS[rl] : 'var(--muted)';
  const riskBg = rl ? RISK_BG[rl] : 'var(--line)';
  const delayProb = prediction?.delay_probability ?? p?.delay_probability;
  const confidence = prediction?.confidence ?? p?.confidence;
  const factors = shapFeatures.length > 0 ? shapFeatures.map(f => ({
    feature: f.display_name ?? f.feature,
    contribution: f.shap_value * 100,
    pct: Math.abs(f.shap_value * 100),
    direction: f.direction,
    value: f.feature_value,
    description: f.description,
  })) : [];

  // ── Current stage index ──────────────────────────────────────────────────
  const currentStageIdx = stages.findIndex(s =>
    s.toLowerCase() === (p?.current_stage ?? '').toLowerCase() ||
    (p?.current_stage ?? '').toLowerCase().includes(s.split(' ')[0].toLowerCase())
  );
  const safeIdx = currentStageIdx >= 0 ? currentStageIdx : -1;

  async function recordAction(
    actionType: string,
    actionPriority: 'Critical' | 'High' | 'Medium' | 'Low',
    note?: string,
  ) {
    if (!p) return;
    setActionSaving(true);
    setPredictionError('');
    try {
      await createProjectAction(p.id, {
        action_type: actionType,
        assigned_to: assignedTo || 'Unassigned',
        priority: actionPriority,
        due_date: dueDate || null,
        notes: note || interventionNote || null,
      });
      setModal(false);
      setToast(`${actionType} saved to the project workflow.`);
      setTimeout(() => setToast(''), 3500);
    } catch (e) {
      setProjectError(e instanceof ApiError ? e.message : 'Unable to save workflow action.');
    } finally {
      setActionSaving(false);
    }
  }


  // Loading / Error states
  if (loadingProject) return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 300 }}>
      <RefreshCw size={20} style={{ animation: 'spin 1s linear infinite', color: 'var(--muted)' }} />
      <span style={{ marginLeft: 10, color: 'var(--muted)' }}>Loading project…</span>
    </div>
  );
  if (projectError || !p) return (
    <div className="page">
      <Link href="/projects" className="link" style={{ fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 5, marginBottom: 16 }}><ArrowLeft size={13} /> Back to Projects</Link>
      <div style={{ padding: '20px', background: 'var(--red-bg)', border: '1px solid var(--red)', borderRadius: 8, color: 'var(--red-text)' }}>
        <AlertCircle size={16} style={{ display: 'inline', marginRight: 8 }} />
        {projectError || 'Project not found.'}
      </div>
    </div>
  );

  const recs = factors
    .filter(f => f.direction === 'up')
    .slice(0, 5)
    .map(f => ({
      title: `Review ${f.feature}`,
      priority: Math.abs(f.contribution) >= 0.15 ? 'High' : 'Medium',
      impact: 'Evidence-based review',
      owner: 'Designated project authority',
      expected: f.description,
    }));


  function handleExport(format: ExportFormat) {
    if (!p) return;
    const headers = ['Metric / Parameter', 'Status / Value', 'Context / Statutory Note'];
    const rows: (string | number)[][] = [
      ['Project Code', p.project_code, 'Corridor identifier'],
      ['Project Name', p.name, `${p.project_type} corridor`],
      ['Administrative Region', `${p.district}, ${p.state}`, `${p.authority}`],
      ['Current Stage', p.current_stage ?? '', 'Statutory milestone under RFCTLARR 2013'],
      ['AI Risk Score', riskScore != null ? `${riskScore.toFixed(1)} / 100` : 'Not predicted', `Classification: ${rl ?? 'Not scored'}`],
      ['Delay Probability', delayProb != null ? `${(delayProb * 100).toFixed(1)}%` : 'Not predicted', 'Estimated delay probability'],
      ['Primary Delay Driver', p.primary_driver ?? '', 'Key bottleneck identified by AI surveillance'],
      ['Affected Families', `${p.affected_families} Families`, 'R&R entitlement register'],
      ['Compensation Status', p.compensation_status ?? '', 'Section 30 status'],
      ['Active Court Cases', `${p.legal_case_count ?? 0} Active Writs`, 'High Court stay / injunction exposure'],
      ['Approval Status', p.approval_pending ? 'Pending Clearances' : 'Cleared', 'Forest / Environment / Wildlife'],
      ...factors.map(f => [
        `Risk Factor: ${f.feature}`,
        `${f.direction === 'up' ? '+' : '-'}${Math.abs(f.contribution).toFixed(1)} score impact (${f.pct.toFixed(1)}%)`,
        `Current value: ${String(f.value ?? 'N/A')}`
      ])
    ];

    const filename = `geomatrix-project-${p.project_code.toLowerCase()}`;
    if (format === 'csv') exportToCSV(`${filename}.csv`, headers, rows);
    else if (format === 'excel') exportToExcel(`${filename}.xls`, p.project_code.slice(0, 31), headers, rows, `Geomatrix Project Dossier: ${p.name} (${p.project_code})`);
    else if (format === 'pdf') {
      const kpis = [
        { label: 'Risk Score', value: riskScore != null ? `${riskScore.toFixed(1)}/100` : 'N/A' },
        { label: 'Delay Prob', value: delayProb != null ? `${(delayProb * 100).toFixed(1)}%` : 'N/A' },
        { label: 'Affected Families', value: String(p.affected_families) },
      ];
      exportToPDF(`Project Risk Dossier: ${p.project_code}`, `${p.name} · ${p.district}, ${p.state} · Stage: ${p.current_stage ?? ''}`, headers, rows, `${filename}.pdf`, kpis);
    }
  }

  return (
    <div className="page">
      {/* ── Breadcrumb ───────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 14 }}>
        <Link href="/projects" className="link" style={{ fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 5 }}>
          <ArrowLeft size={13} /> Back to Projects
        </Link>
      </div>

      {/* ── Missing Fields Warning ────────────────────────────────────── */}
      {missingFields.length > 0 && (
        <div style={{ padding: '10px 16px', background: 'var(--amber-bg)', border: '1px solid var(--amber)', borderRadius: 8, marginBottom: 16, fontSize: 13, color: 'var(--amber-text)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <FileWarning size={14} />
          <strong>Prediction unavailable:</strong> {missingFields.length} required field(s) missing — {missingFields.join(', ')}.
          <span style={{ color: 'var(--muted)', fontSize: 12 }}>Edit the project to add these fields, then run prediction.</span>
        </div>
      )}

      {/* ── Prediction Error ─────────────────────────────────────────── */}
      {predictionError && (
        <div style={{ padding: '10px 16px', background: 'var(--red-bg)', border: '1px solid var(--red)', borderRadius: 8, marginBottom: 16, fontSize: 13, color: 'var(--red-text)', display: 'flex', gap: 8, alignItems: 'center' }}>
          <AlertCircle size={14} />{predictionError}
        </div>
      )}

      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="head" style={{ marginBottom: 0 }}>
        <div>
          <div className="eyebrow">
            <Brain size={11} style={{ display: 'inline', marginRight: 4 }} />
            AI Risk Intelligence · {p.project_code}
          </div>
          <h1 className="h1" style={{ margin: '4px 0 6px' }}>{p.name}</h1>
          <div className="sub" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
            <span><MapPin size={11} style={{ display: 'inline' }} /> {p.district}, {p.state}</span>
            <span>·</span><span>{p.authority}</span>
            <span>·</span><span>{p.project_type}</span>
            <span>·</span><span style={{ fontWeight: 600 }}>Stage: {p.current_stage ?? '—'}</span>
          </div>
        </div>
        <div className="actions">
          <ExportDropdown label="Export" onExport={handleExport} tooltip="Export Project Dossier (PDF, Excel, CSV)" />
          <Link className="btn" href="/map"><MapPin size={12} /> GIS View</Link>
          <button
            className="btn"
            onClick={handleRunPrediction}
            disabled={runningPrediction || missingFields.length > 0}
            title={missingFields.length > 0 ? `Missing: ${missingFields.join(', ')}` : 'Run ML risk prediction using stored project data'}
          >
            {runningPrediction
              ? <RefreshCw size={13} style={{ animation: 'spin 1s linear infinite' }} />
              : <Activity size={13} />}
            {runningPrediction ? 'Running…' : 'Run Risk Prediction'}
          </button>
          <button className="btn" onClick={handleDeleteProject} style={{ background: 'rgba(239,68,68,0.08)', color: 'var(--red-text)', border: '1px solid rgba(239,68,68,0.25)' }}>
            <Trash2 size={13} /> Delete
          </button>
          <button className="btn primary" onClick={() => setModal(true)}>
            <Zap size={13} /> Assign Intervention
          </button>
        </div>
      </div>

      {/* ── Hero Risk Panel ───────────────────────────────────────────────── */}
      <div style={{
        margin: '18px 0', padding: '20px 24px',
        background: riskBg, border: `1.5px solid ${riskColor}30`,
        borderLeft: `4px solid ${riskColor}`,
        borderRadius: 10,
      }}>
        <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          {/* Risk Score */}
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>AI Composite Risk Score</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
              <span style={{ fontSize: 52, fontWeight: 900, color: riskColor, lineHeight: 1 }}>
                {riskScore != null ? riskScore.toFixed(1) : '—'}
              </span>
              <span style={{ color: 'var(--muted)', fontSize: 16 }}>/100</span>
              <RiskBadge score={riskScore ?? 0} />
            </div>
            {riskScore == null && (
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Run prediction to compute risk score</div>
            )}
          </div>

          {/* Key Metrics */}
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            {([
              ['Delay Probability', delayProb != null ? `${(delayProb * 100).toFixed(1)}%` : '—', 'of project exceeding threshold', riskColor],
              ['Predicted Delay', prediction?.predicted_delay_days != null ? `${prediction.predicted_delay_days} days` : '—', 'most likely scenario', '#ea580c'],
              ['Confidence', confidence != null ? `${(confidence * 100).toFixed(0)}%` : '—', 'model confidence', confidence != null && confidence > 0.88 ? 'var(--green)' : 'var(--amber)'],
            ] as [string, string, string, string][]).map(([label, val, sub, color]) => (
              <div key={label} style={{ textAlign: 'center', minWidth: 100 }}>
                <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 22, fontWeight: 900, color, lineHeight: 1 }}>{val}</div>
                <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>{sub}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Primary driver + disclaimer */}
        <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, fontSize: 13, color: 'var(--ink-secondary)' }}>
            <strong>Primary Risk Driver:</strong> {p.primary_driver ?? 'Not yet predicted'}
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted)', padding: '4px 10px', background: 'var(--bg)', borderRadius: 4, border: '1px solid var(--line)' }}>
            ⚠ AI decision support — final authority rests with designated officers under RFCTLARR 2013
          </div>
        </div>
      </div>

      {/* ── KPI Strip ────────────────────────────────────────────────────── */}
      <div className="grid" style={{ gridTemplateColumns: 'repeat(5,1fr)', gap: 12, marginBottom: 20 }}>
        <MetricCard label="Land Area" value={(p.land_required ?? 0).toLocaleString() + ' ha'} color="var(--blue)" />
        <MetricCard label="Affected Families" value={(p.affected_families ?? 0).toLocaleString()} color={(p.affected_families ?? 0) > 150 ? 'var(--red)' : 'var(--amber)'} />
        <MetricCard label="Overdue Milestones" value={String(p.overdue_milestones ?? 0)} color={(p.overdue_milestones ?? 0) > 15 ? 'var(--red)' : 'var(--amber)'} sub="milestone breaches" />
        <MetricCard label="Open Legal Cases" value={String(p.legal_case_count ?? 0)} color={(p.legal_case_count ?? 0) > 5 ? 'var(--red)' : (p.legal_case_count ?? 0) > 0 ? 'var(--amber)' : 'var(--green)'} />
        <MetricCard label="Objections Filed" value={String(p.objection_count ?? 0)} color={(p.objection_count ?? 0) > 10 ? 'var(--red)' : 'var(--amber)'} sub="pending resolution" />
      </div>

      {/* ── Tab Navigation ───────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 20, borderBottom: '2px solid var(--line)', overflowX: 'auto' }}>
        {TABS.map(({ key, label, icon: Icon }) => (
          <button key={key} onClick={() => setActiveTab(key)} style={{
            background: 'none', border: 'none', padding: '11px 18px', cursor: 'pointer',
            fontSize: 13, fontWeight: activeTab === key ? 700 : 500, whiteSpace: 'nowrap',
            color: activeTab === key ? 'var(--blue)' : 'var(--muted)',
            borderBottom: activeTab === key ? '2px solid var(--blue)' : '2px solid transparent',
            marginBottom: -2, display: 'inline-flex', alignItems: 'center', gap: 7, transition: 'all .15s'
          }}>
            <Icon size={13} /> {label}
          </button>
        ))}
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: AI Risk Analysis (SHAP)
      ══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'shap' && (
        <div className="grid two">
          {/* SHAP Drivers */}
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Top Risk Drivers — SHAP Contribution</div>
                <div className="muted">Why is this project at risk? Feature-level attribution.</div>
              </div>
              <span className="tag">EXPLAINABLE AI</span>
            </div>

            {factors.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--muted)', fontSize: 13 }}>
                <Brain size={28} style={{ marginBottom: 10, opacity: 0.3 }} />
                <div style={{ fontWeight: 600 }}>No prediction yet</div>
                <div style={{ fontSize: 12, marginTop: 4 }}>Run risk prediction to see SHAP feature attribution</div>
              </div>
            ) : factors.slice(0, 6).map(f => (
              <div key={f.feature} style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span style={{ fontWeight: 600 }}>{f.feature}</span>
                  <span style={{ fontWeight: 800, fontSize: 12, color: f.contribution > 0 ? '#dc2626' : '#15803d' }}>
                    {f.contribution > 0 ? '+' : ''}{f.contribution.toFixed(1)} pts · {f.pct.toFixed(1)}%
                  </span>
                </div>
                <div style={{ height: 10, background: 'var(--line)', borderRadius: 5, overflow: 'hidden' }}>
                  <div style={{
                    width: Math.min(100, Math.abs(f.pct)) + '%',
                    height: '100%', borderRadius: 5, transition: 'width 0.6s ease',
                    background: f.contribution > 0
                      ? `linear-gradient(90deg, #dc2626, #ef4444)`
                      : `linear-gradient(90deg, #15803d, #22c55e)`
                  }} />
                </div>
              </div>
            ))}

            {/* AI Explanation block with Gemini */}
            <div style={{ marginTop: 18, padding: '14px 16px', background: 'var(--blue-light)', border: '1px solid var(--blue-border)', borderRadius: 8 }}>
              <div style={{ fontWeight: 800, fontSize: 12, color: 'var(--blue)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 5, justifyContent: 'space-between' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}><Brain size={13} /> AI Narrative Explanation</span>
                <button
                  onClick={handleGeminiExplain}
                  disabled={geminiLoading}
                  style={{ background: 'var(--blue)', color: '#fff', border: 'none', borderRadius: 5, padding: '4px 10px', fontSize: 11, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
                  title="Explain this project's risk with Google Gemini AI"
                >
                  {geminiLoading ? <RefreshCw size={11} style={{ animation: 'spin 1s linear infinite' }} /> : <Sparkles size={11} />}
                  {geminiLoading ? 'Asking Gemini…' : 'Explain with Gemini AI'}
                </button>
              </div>

              {geminiError && (
                <div style={{ fontSize: 12, color: 'var(--red-text)', marginBottom: 8 }}>{geminiError}</div>
              )}

              {geminiResult ? (
                <p className="sub" style={{ lineHeight: 1.75, margin: 0, whiteSpace: 'pre-line' }}>{geminiResult}</p>
              ) : factors.length > 0 ? (
                <p className="sub" style={{ lineHeight: 1.75, margin: 0 }}>
                  This project is classified as <strong>{rl} RISK (score: {riskScore?.toFixed(1)}/100)</strong> with a{' '}
                  <strong>{delayProb != null ? `${(delayProb * 100).toFixed(1)}%` : '—'} probability of delay</strong>.
                  {factors[0] && <> The most significant contributor is <strong>{factors[0].feature} ({factors[0].pct.toFixed(1)}%)</strong></>}
                  {factors[1] && <>, followed by <strong>{factors[1].feature} ({factors[1].pct.toFixed(1)}%)</strong></>}.
                  {' '}Click &quot;Explain with Gemini AI&quot; for a full decision-support narrative.
                </p>
              ) : (
                <p className="sub" style={{ lineHeight: 1.75, margin: 0, color: 'var(--muted)' }}>
                  Run risk prediction first to generate an AI explanation.
                </p>
              )}
            </div>
          </div>

          {/* Risk Transitions + "Why Now?" */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div className="panel">
              <div className="panelhead">
                <div>
                  <div className="paneltitle">Risk Transitions — Why Now?</div>
                  <div className="muted">When and why risk level changed</div>
                </div>
              </div>
              <div style={{ color: 'var(--muted)', fontSize: 13, padding: '12px 0', lineHeight: 1.6 }}>
                {prediction ? (
                  <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: riskColor, marginTop: 5, flexShrink: 0 }} />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: 'var(--ink)' }}>
                        {riskScore != null && rl ? <>Risk scored at {riskScore.toFixed(1)} / 100 · {rl}</> : 'No risk score recorded'}
                      </div>
                      <div style={{ fontSize: 12, marginTop: 2 }}>
                        Predicted on {new Date().toLocaleDateString('en-IN')} · Confidence: {confidence != null ? `${(confidence * 100).toFixed(0)}%` : '—'}
                      </div>
                    </div>
                  </div>
                ) : 'Run risk prediction to see transition history.'}
              </div>
            </div>

            {/* Audit Trail preview */}
            <div className="panel">
              <div className="panelhead">
                <div>
                  <div className="paneltitle">Project Data Summary</div>
                  <div className="muted">Stored field values for prediction</div>
                </div>
              </div>
              {([
                ['Compensation Status', p.compensation_status],
                ['R&R Status', p.rr_status],
                ['Env Clearance', p.env_clearance_status],
                ['Forest Clearance', p.forest_clearance_status],
                ['CRZ Status', p.crz_status],
                ['Doc Completeness', p.doc_completeness_pct != null ? `${p.doc_completeness_pct}%` : null],
              ] as [string, string | null | undefined][]).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '7px 0', borderBottom: '1px solid var(--line)', alignItems: 'center' }}>
                  <span style={{ color: 'var(--muted)', fontWeight: 700 }}>{k}</span>
                  <span style={{ color: v ? 'var(--ink)' : 'var(--muted)', fontWeight: 600, fontSize: 12 }}>
                    {v ?? <em>Not set</em>}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: Forecast & Prediction
      ══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'forecast' && (
        <div className="grid two">
          {/* Risk Prediction Results */}
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Risk Prediction Results</div>
                <div className="muted">Output from the most recent model run</div>
              </div>
            </div>
            {!prediction ? (
              <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--muted)', fontSize: 13 }}>
                <Activity size={28} style={{ marginBottom: 10, opacity: 0.3 }} />
                <div style={{ fontWeight: 600 }}>No prediction yet</div>
                <div style={{ fontSize: 12, marginTop: 4 }}>Click &quot;Run Risk Prediction&quot; to compute delay and risk forecast</div>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 12 }}>
                {([
                  ['Risk Score', prediction.risk_score != null ? `${prediction.risk_score.toFixed(1)} / 100` : '—', riskColor],
                  ['Risk Level', prediction.risk_level, riskColor],
                  ['Delay Probability', prediction.delay_probability != null ? `${(prediction.delay_probability * 100).toFixed(1)}%` : '—', 'var(--orange)'],
                  ['Predicted Delay', prediction.predicted_delay_days != null ? `${prediction.predicted_delay_days} days` : '—', 'var(--orange)'],
                  ['Model Confidence', prediction.confidence != null ? `${(prediction.confidence * 100).toFixed(0)}%` : '—', prediction.confidence != null && prediction.confidence > 0.88 ? 'var(--green)' : 'var(--amber)'],
                ] as [string, string, string][]).map(([k, v, c]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--line)', alignItems: 'center' }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--ink-secondary)' }}>{k}</span>
                    <span style={{ fontSize: 16, fontWeight: 800, color: c }}>{v}</span>
                  </div>
                ))}
                <div style={{ marginTop: 8, padding: '10px 14px', background: 'var(--bg)', borderRadius: 6, border: '1px solid var(--line)', fontSize: 12, color: 'var(--muted)' }}>
                  Predicted on {new Date().toLocaleDateString('en-IN')} · Model: {prediction.model_version ?? 'active_model'} · Run ID: {prediction.model_run_id?.slice(0, 8) ?? 'N/A'}
                </div>
              </div>
            )}
          </div>

          {/* SHAP Bar Chart (when available) */}
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Feature Impact (SHAP)</div>
                <div className="muted">Contribution of each feature to the risk score</div>
              </div>
              <span className="tag">MODEL VALIDATION</span>
            </div>
            {factors.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--muted)', fontSize: 13 }}>
                <Database size={28} style={{ marginBottom: 10, opacity: 0.3 }} />
                <div>Run prediction to view feature impact chart</div>
              </div>
            ) : (
              <div className="chart" style={{ height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={factors.slice(0, 8).map(f => ({ name: f.feature.slice(0, 16), impact: Math.abs(f.contribution) }))}
                    layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 80 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--chart-grid)" />
                    <XAxis type="number" fontSize={10} tick={{ fill: 'var(--chart-text)' }} />
                    <YAxis dataKey="name" type="category" width={80} fontSize={9} tick={{ fill: 'var(--chart-text)' }} />
                    <Tooltip contentStyle={{ background: 'var(--surface)', border: '1px solid var(--line)', borderRadius: 6, fontSize: 12 }} />
                    <Bar dataKey="impact" radius={[0, 4, 4, 0]}>
                      {factors.slice(0, 8).map((f, i) => (
                        <Cell key={i} fill={f.contribution > 0 ? '#dc2626' : '#15803d'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: What-If Simulator
      ══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'simulator' && (
  <div className="panel">
    <div className="panelhead">
      <div>
        <div className="paneltitle">What-If Simulator</div>
        <div className="muted">Counterfactual simulation is disabled until a validated counterfactual model is deployed.</div>
      </div>
      <span className="tag">UNAVAILABLE</span>
    </div>
    <div style={{ padding: '24px 8px', lineHeight: 1.7, color: 'var(--muted)' }}>
      The current production model provides an observed risk estimate for the supplied project state.
      It does not provide causal intervention effects, so the application will not manufacture a simulated
      risk score or delay-days estimate. A separately validated counterfactual model can be integrated here.
    </div>
  </div>
)}

{activeTab === 'intervention' && (
        <div>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(340px,1fr))', gap: 16, marginBottom: 20 }}>
            {recs.map((r, i) => (
              <div key={r.title} className="panel" style={{ borderLeft: `3px solid ${i === 0 ? '#dc2626' : i === 1 ? '#ea580c' : '#d97706'}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span className={'risk ' + r.priority.toLowerCase()}>{r.priority}</span>
                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>Priority #{i + 1}</span>
                </div>
                <h4 style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 800 }}>{r.title}</h4>
                <div style={{ fontSize: 13, color: 'var(--ink-secondary)', lineHeight: 1.6, marginBottom: 12 }}>
                  <div><User size={11} style={{ display: 'inline' }} /> <strong>Responsible Unit:</strong> {r.owner}</div>
                  <div><Target size={11} style={{ display: 'inline' }} /> <strong>Expected Impact:</strong> {r.expected}</div>
                </div>
                <div className="actions">
                  <button className="btn" onClick={() => setModal(true)}>Assign Officer</button>
                  <button className="btn" onClick={() => recordAction('Task', r.priority === 'High' ? 'High' : 'Medium', r.expected)}>Create Task</button>
                  <button className="btn" onClick={() => recordAction('Escalation', 'Critical', r.expected)}>Escalate</button>
                </div>
              </div>
            ))}
          </div>

          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Recovery Precedents</div>
                <div className="muted">Only verified comparable-project records should appear here.</div>
              </div>
              <span className="tag">NO VERIFIED DATA</span>
            </div>
            <div style={{ padding: '24px 8px', color: 'var(--muted)', lineHeight: 1.7 }}>
              No verified comparable-project outcome dataset is currently connected.
              GEOMATRIX does not display invented project precedents, intervention outcomes or days saved.
            </div>
          </div>
        </div>
      )}
      {/* ══════════════════════════════════════════════════════════════════════
          TAB: Acquisition Pipeline
      ══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'timeline' && (
        <div className="grid two">
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Acquisition Stage Pipeline</div>
                <div className="muted">Status is shown from the project's recorded current stage only.</div>
              </div>
            </div>
            <div style={{ display: 'grid', gap: 8 }}>
              {stages.map((stage, i) => {
                const isCompleted = safeIdx >= 0 && i < safeIdx;
                const isCurrent = safeIdx >= 0 && i === safeIdx;
                return (
                  <div key={stage} style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '11px 13px', border: '1px solid var(--line)',
                    borderRadius: 8, background: isCurrent ? 'var(--blue-light)' : 'var(--bg)',
                  }}>
                    <div style={{
                      width: 24, height: 24, borderRadius: '50%', display: 'grid', placeItems: 'center',
                      background: isCompleted ? 'var(--green-bg)' : isCurrent ? 'var(--blue-light)' : 'var(--line)',
                      color: isCompleted ? 'var(--green)' : isCurrent ? 'var(--blue)' : 'var(--muted)',
                      fontSize: 11, fontWeight: 800,
                    }}>
                      {isCompleted ? '✓' : i + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: 13 }}>{stage}</div>
                      <div className="muted" style={{ fontSize: 11 }}>
                        {isCurrent ? 'Current recorded stage' : isCompleted ? 'Earlier stage in the configured process' : safeIdx < 0 ? 'No stage transition inferred' : 'Later stage'}
                      </div>
                    </div>
                    {isCurrent && <span className="tag">CURRENT</span>}
                  </div>
                );
              })}
            </div>
          </div>

          <div className="panel">
            <div className="paneltitle">Stage-level Risk</div>
            <div className="muted" style={{ marginTop: 10, lineHeight: 1.7 }}>
              No independently validated stage-level risk model is deployed. GEOMATRIX therefore does not assign fixed risk scores to acquisition stages.
            </div>
            <div style={{ marginTop: 22, padding: 18, borderRadius: 10, background: 'var(--bg)', border: '1px dashed var(--line)', textAlign: 'center' }}>
              <div style={{ fontSize: 30, fontWeight: 900, color: riskColor }}>
                {riskScore == null ? '—' : riskScore.toFixed(1)}
              </div>
              <div className="muted">Current project risk score / 100</div>
              <div style={{ marginTop: 7, fontSize: 12 }}>
                {riskScore == null ? 'No validated project prediction recorded' : `Current level: ${rl}`}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          TAB: Data Lineage
      ══════════════════════════════════════════════════════════════════════ */}
      {activeTab === 'lineage' && (
        <div className="grid two">
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Data Lineage & Provenance</div>
                <div className="muted">Sources and quality for this prediction</div>
              </div>
              <span className="tag">TRANSPARENCY</span>
            </div>
            <div style={{ display: 'grid', gap: 12, marginBottom: 20 }}>
              {([
                ['Data Source', p.source_name || (p.source_url ? 'External ingestion source' : 'Not recorded')],
                ['Last Updated', p.updated_at ? new Date(p.updated_at).toLocaleDateString('en-IN') : (p.imported_at ? new Date(p.imported_at).toLocaleDateString('en-IN') : 'Not recorded')],
                ['Validation Status', p.validation_status ?? 'Not recorded'],
                ['Data Classification', p.data_classification ?? 'Not recorded'],
                ['Document Completeness', p.doc_completeness_pct == null ? 'Not recorded' : `${p.doc_completeness_pct}%`],
                ['Model Confidence', confidence != null ? `${(confidence * 100).toFixed(1)}%` : 'Pending prediction'],
              ] as [string, string][]).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
                  <span style={{ color: 'var(--muted)', fontWeight: 700 }}>{k}</span>
                  <span style={{ color: 'var(--ink)', fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{v}</span>
                </div>
              ))}
            </div>

            <div className="paneltitle" style={{ marginBottom: 10 }}>Features Used in Prediction</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {['Land Required', 'Affected Families', 'Current Stage', 'Compensation Status', 'Legal Cases', 'Objections', 'Clearances', 'Overdue Milestones'].map(f => (
                <span key={f} style={{ fontSize: 12, fontWeight: 600, padding: '4px 10px', background: 'var(--blue-light)', color: 'var(--blue)', borderRadius: 4, border: '1px solid var(--blue-border)' }}>
                  {f}
                </span>
              ))}
            </div>

            <div style={{ marginTop: 16 }}>
              <div style={{ marginBottom: 6, display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600 }}>
                <span>Data Completeness</span>
                <span style={{ color: p.doc_completeness_pct != null && p.doc_completeness_pct >= 80 ? 'var(--green)' : 'var(--amber)' }}>
                  {p.doc_completeness_pct}%
                </span>
              </div>
              <div style={{ height: 10, background: 'var(--line)', borderRadius: 5, overflow: 'hidden' }}>
                <div style={{ width: `${p.doc_completeness_pct ?? 0}%`, height: '100%', background: p.doc_completeness_pct != null && p.doc_completeness_pct >= 80 ? 'var(--green)' : 'var(--amber)', borderRadius: 5, transition: 'width 0.6s ease' }} />
              </div>
            </div>
          </div>

          {/* Full audit trail */}
          <div className="panel">
            <div className="panelhead">
              <div>
                <div className="paneltitle">Complete Audit Trail</div>
                <div className="muted">Persisted project actions, predictions and record changes.</div>
              </div>
              <span className="tag">{auditEntries.length} EVENTS</span>
            </div>
            {auditEntries.length === 0 ? (
              <div className="muted" style={{ padding: '20px 4px' }}>
                No persisted audit events are available for this project.
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 14 }}>
                {auditEntries.map((evt) => (
                  <div key={evt.id} style={{ display: 'flex', gap: 12, paddingBottom: 14, borderBottom: '1px solid var(--line)' }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', display: 'grid', placeItems: 'center',
                      background: 'var(--blue-light)', color: 'var(--blue)', flexShrink: 0,
                    }}>
                      <Database size={13} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 700, fontSize: 13 }}>{evt.action}</div>
                      <div className="muted" style={{ fontSize: 11, marginTop: 3 }}>
                        {evt.actor_email || 'System'} · {new Date(evt.timestamp).toLocaleString('en-IN')}
                      </div>
                      <div style={{ fontSize: 11, marginTop: 5, color: 'var(--ink-secondary)' }}>
                        {evt.entity_type} · {evt.entity_id}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Intervention Modal ────────────────────────────────────────────── */}
      {modal && (
        <div className="modalbg" onClick={() => setModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 480 }}>
            <h3 style={{ margin: '0 0 6px', fontWeight: 800 }}>Assign Intervention</h3>
            <p className="sub" style={{ marginBottom: 18 }}>
              Record an intervention for <strong>{p.name}</strong>.
              &nbsp;<em style={{ fontSize: 11 }}>This action is persisted to the project workflow and audit trail.</em>
            </p>
            <div className="form">
              <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>Assigned Officer / Unit</label>
              <input value={assignedTo} onChange={e => setAssignedTo(e.target.value)} />
              <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>Priority Level</label>
              <select value={priority} onChange={e => setPriority(e.target.value as 'Critical' | 'High' | 'Medium' | 'Low')}>
                <option value="Critical">Critical — Immediate action</option>
                <option value="High">High — Action within 48 hours</option>
                <option value="Medium">Medium — Action within 7 days</option>
                <option value="Low">Low — Routine follow-up</option>
              </select>
              <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>Due Date</label>
              <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)} />
              <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--muted)' }}>Intervention Notes</label>
              <textarea rows={3} value={interventionNote || `Fast-track resolution of ${p.primary_driver || 'compensation backlog'}. Convene inter-departmental review within 5 working days.`} onChange={e => setInterventionNote(e.target.value)} />
              <div className="actions" style={{ justifyContent: 'flex-end', marginTop: 6 }}>
                <button className="btn" onClick={() => setModal(false)}>Cancel</button>
                <button className="btn primary" disabled={actionSaving} onClick={() => recordAction('Intervention', priority)}>
                  <CheckCircle2 size={13} /> {actionSaving ? 'Saving…' : 'Confirm & Record'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Toast ─────────────────────────────────────────────────────────── */}
      {toast && (
        <div style={{ position: 'fixed', right: 20, bottom: 20, background: 'var(--navy)', color: '#fff', padding: '13px 20px', borderRadius: 8, fontSize: 13, zIndex: 60, display: 'flex', alignItems: 'center', gap: 8, boxShadow: '0 8px 25px rgba(0,0,0,0.25)', animation: 'fadeIn 0.3s ease' }}>
          <CheckCircle2 size={15} style={{ color: '#4ade80' }} /> {toast}
        </div>
      )}
    </div>
  );
}
